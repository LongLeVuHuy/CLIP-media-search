import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


WATCH_FOLDER = "input_media"
DATABASE_FILE = "media_clip.json"

IMAGE_MODEL_NAME = "sentence-transformers/clip-ViT-B-32"
TEXT_MODEL_NAME = "sentence-transformers/clip-ViT-B-32-multilingual-v1"

VIDEO_SAMPLE_INTERVAL_SECONDS = 5.0
VIDEO_MAX_FRAMES = 60
ENCODE_BATCH_SIZE = 16

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_image_model: Optional[SentenceTransformer] = None
_text_model: Optional[SentenceTransformer] = None


def print_device_info() -> None:
    print("=" * 60, flush=True)
    print("THÔNG TIN THIẾT BỊ", flush=True)
    print("=" * 60, flush=True)
    print(f"Thiết bị PyTorch: {DEVICE}", flush=True)

    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            vram_gb = props.total_memory / (1024 ** 3)
            print(
                f"GPU {index}: {torch.cuda.get_device_name(index)} "
                f"({vram_gb:.1f} GB VRAM)",
                flush=True,
            )
        print(f"CUDA: {torch.version.cuda}", flush=True)
    else:
        print("Không phát hiện GPU CUDA, chương trình dùng CPU.", flush=True)


def get_image_model() -> SentenceTransformer:
    global _image_model
    if _image_model is None:
        print(f"Đang tải CLIP image model trên {DEVICE}...", flush=True)
        _image_model = SentenceTransformer(IMAGE_MODEL_NAME, device=DEVICE)
        print("Đã tải CLIP image model.", flush=True)
    return _image_model


def get_text_model() -> SentenceTransformer:
    """Được file search_media.py sử dụng khi tìm kiếm."""
    global _text_model
    if _text_model is None:
        print(f"Đang tải CLIP text model trên {DEVICE}...", flush=True)
        _text_model = SentenceTransformer(TEXT_MODEL_NAME, device=DEVICE)
        print("Đã tải CLIP text model.", flush=True)
    return _text_model


def load_database() -> List[Dict[str, Any]]:
    if not os.path.exists(DATABASE_FILE):
        save_database([])
        return []

    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as error:
        print(f"Không đọc được {DATABASE_FILE}: {error}", flush=True)
        return []


def save_database(data):
    temporary_file = DATABASE_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    for attempt in range(5):
        try:
            os.replace(temporary_file, DATABASE_FILE)
            return
        except PermissionError:
            if attempt == 4:
                raise
            print("File JSON đang bị khóa, thử lại sau 1 giây...")
            time.sleep(1)


def generate_id(data: List[Dict[str, Any]]) -> int:
    return 1 if not data else max(int(item.get("id", 0)) for item in data) + 1


def file_already_exists(file_path: str, data: List[Dict[str, Any]]) -> bool:
    normalized = os.path.normcase(os.path.abspath(file_path))
    return any(
        os.path.normcase(os.path.abspath(str(item.get("file_path", ""))))
        == normalized
        for item in data
    )


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    return vector if norm == 0 else vector / norm


def encode_images(images: List[Image.Image]) -> np.ndarray:
    if not images:
        return np.empty((0, 0), dtype=np.float32)

    rgb_images = [image.convert("RGB") for image in images]
    embeddings = get_image_model().encode(
        rgb_images,
        batch_size=ENCODE_BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype=np.float32)


def encode_text(query: str) -> np.ndarray:
    """Được file search_media.py sử dụng."""
    embedding = get_text_model().encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return normalize_vector(embedding)


def analyze_image(file_path: str) -> Dict[str, Any]:
    with Image.open(file_path) as image:
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        embedding = encode_images([rgb_image])[0]

    return {
        "clip_embedding": embedding.tolist(),
        "width": width,
        "height": height,
    }


def build_video_timestamps(
    duration_seconds: float,
    interval_seconds: float,
    max_frames: int,
) -> List[float]:
    if duration_seconds <= 0:
        return [0.0]

    timestamps = np.arange(
        0.0,
        duration_seconds,
        max(interval_seconds, 0.1),
        dtype=np.float32,
    ).tolist()

    last_timestamp = max(duration_seconds - 0.05, 0.0)
    if not timestamps or abs(timestamps[-1] - last_timestamp) > 0.5:
        timestamps.append(last_timestamp)

    if len(timestamps) > max_frames:
        indices = np.linspace(0, len(timestamps) - 1, max_frames, dtype=int)
        timestamps = [timestamps[index] for index in indices]

    return [round(float(timestamp), 3) for timestamp in timestamps]


def extract_video_frames(
    file_path: str,
    interval_seconds: float = VIDEO_SAMPLE_INTERVAL_SECONDS,
    max_frames: int = VIDEO_MAX_FRAMES,
) -> Tuple[List[Image.Image], List[float], float]:
    video = cv2.VideoCapture(file_path)
    if not video.isOpened():
        raise ValueError("Không thể mở video.")

    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(video.get(cv2.CAP_PROP_FPS))
    duration = frame_count / fps if frame_count > 0 and fps > 0 else 0.0

    timestamps = build_video_timestamps(duration, interval_seconds, max_frames)
    frames: List[Image.Image] = []
    valid_timestamps: List[float] = []

    try:
        for timestamp in timestamps:
            video.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
            success, frame = video.read()
            if not success:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(frame_rgb))
            valid_timestamps.append(timestamp)
    finally:
        video.release()

    return frames, valid_timestamps, duration


def analyze_video(file_path: str) -> Dict[str, Any]:
    frames, timestamps, duration = extract_video_frames(file_path)
    if not frames:
        raise ValueError("Không lấy được khung hình nào từ video.")

    embeddings = encode_images(frames)
    pooled_embedding = normalize_vector(embeddings.mean(axis=0))

    frame_data = [
        {
            "timestamp_seconds": timestamp,
            "clip_embedding": embedding.tolist(),
        }
        for timestamp, embedding in zip(timestamps, embeddings)
    ]

    return {
        "clip_embedding": pooled_embedding.tolist(),
        "frame_embeddings": frame_data,
        "duration_seconds": round(duration, 2),
        "analyzed_frames": len(frame_data),
        "sample_interval_seconds": VIDEO_SAMPLE_INTERVAL_SECONDS,
    }


def process_media_file(file_path: str) -> None:
    file_path = os.path.abspath(file_path)
    extension = Path(file_path).suffix.lower()

    if extension not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        return

    data = load_database()
    if file_already_exists(file_path, data):
        print(f"Đã có trong cơ sở dữ liệu: {file_path}", flush=True)
        return

    print(f"\nĐang xử lý: {file_path}", flush=True)

    try:
        if extension in IMAGE_EXTENSIONS:
            media_type = "image"
            analysis = analyze_image(file_path)
        else:
            media_type = "video"
            analysis = analyze_video(file_path)

        item: Dict[str, Any] = {
            "id": generate_id(data),
            "media_type": media_type,
            "title": Path(file_path).stem,
            "file_name": Path(file_path).name,
            "file_path": file_path,
            "file_size_bytes": os.path.getsize(file_path),
            "indexed_time": datetime.now().isoformat(timespec="seconds"),
            "embedding_model": IMAGE_MODEL_NAME,
        }
        item.update(analysis)

        data.append(item)
        save_database(data)

        print(f"Đã lập chỉ mục: {media_type} | {Path(file_path).name}", flush=True)
        if media_type == "video":
            print(f"Số frame đã phân tích: {item['analyzed_frames']}", flush=True)

    except Exception as error:
        print(f"Không xử lý được file: {error}", flush=True)


def wait_until_file_ready(file_path: str, timeout: int = 60) -> bool:
    start_time = time.time()
    previous_size = -1
    stable_count = 0

    while time.time() - start_time < timeout:
        if not os.path.exists(file_path):
            time.sleep(1)
            continue

        current_size = os.path.getsize(file_path)
        if current_size == previous_size and current_size > 0:
            stable_count += 1
        else:
            stable_count = 0

        if stable_count >= 2:
            return True

        previous_size = current_size
        time.sleep(1)

    return False


class MediaEventHandler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        if not event.is_directory and wait_until_file_ready(event.src_path):
            process_media_file(event.src_path)

    def on_moved(self, event) -> None:
        if not event.is_directory and wait_until_file_ready(event.dest_path):
            process_media_file(event.dest_path)


def scan_existing_files() -> None:
    for root, _, files in os.walk(WATCH_FOLDER):
        for file_name in files:
            process_media_file(os.path.join(root, file_name))


def watch_folder() -> None:
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    print_device_info()
    print(f"Thư mục theo dõi: {os.path.abspath(WATCH_FOLDER)}", flush=True)
    print(f"Cơ sở dữ liệu: {os.path.abspath(DATABASE_FILE)}", flush=True)

    print("\nĐang quét file hiện có...", flush=True)
    scan_existing_files()

    observer = Observer()
    observer.schedule(MediaEventHandler(), WATCH_FOLDER, recursive=True)
    observer.start()

    print("\nĐang theo dõi thư mục. Nhấn Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nĐang dừng...", flush=True)
        observer.stop()

    observer.join()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lập chỉ mục ảnh/video bằng CLIP."
    )
    parser.add_argument(
        "--scan-once",
        action="store_true",
        help="Quét một lần rồi thoát.",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Xóa dữ liệu cũ và lập chỉ mục lại.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    os.makedirs(WATCH_FOLDER, exist_ok=True)

    if args.reindex:
        print_device_info()
        save_database([])
        print(f"Đã xóa chỉ mục cũ: {DATABASE_FILE}", flush=True)
        scan_existing_files()
        print("Đã lập chỉ mục lại toàn bộ.", flush=True)
        return

    if args.scan_once:
        print_device_info()
        scan_existing_files()
        print("Đã quét xong.", flush=True)
        return

    watch_folder()


if __name__ == "__main__":
    main()