import argparse
import os
import subprocess
from typing import Any, Dict, List, Optional

import numpy as np

from media_manager import (
    encode_text,
    load_database,
    normalize_vector,
    print_device_info,
)


def cosine_score(query_embedding: np.ndarray, media_embedding: List[float]) -> float:
    candidate = normalize_vector(np.asarray(media_embedding, dtype=np.float32))
    if candidate.size != query_embedding.size:
        return -1.0
    return float(np.dot(query_embedding, candidate))


def search_media(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    query = query.strip()
    if not query:
        raise ValueError("Câu tìm kiếm không được để trống.")

    data = load_database()
    if not data:
        print("Cơ sở dữ liệu đang trống.")
        print("Hãy chạy: python media_manager.py --scan-once")
        return []

    query_embedding = encode_text(query)
    results: List[Dict[str, Any]] = []

    for item in data:
        media_embedding = item.get("clip_embedding")
        if not isinstance(media_embedding, list):
            continue

        score = cosine_score(query_embedding, media_embedding)
        best_timestamp: Optional[float] = None

        if item.get("media_type") == "video":
            for frame in item.get("frame_embeddings", []):
                frame_embedding = frame.get("clip_embedding")
                if not isinstance(frame_embedding, list):
                    continue

                frame_score = cosine_score(query_embedding, frame_embedding)
                if frame_score > score:
                    score = frame_score
                    best_timestamp = float(frame.get("timestamp_seconds", 0.0))

        results.append({
            "id": item.get("id"),
            "media_type": item.get("media_type"),
            "title": item.get("title"),
            "file_path": item.get("file_path"),
            "score": score,
            "best_timestamp_seconds": best_timestamp,
        })

    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:max(top_k, 1)]


def format_timestamp(seconds: Optional[float]) -> str:
    if seconds is None:
        return ""
    total_seconds = max(int(round(seconds)), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def print_results(query: str, results: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 72)
    print(f"KẾT QUẢ TÌM KIẾM: {query}")
    print("=" * 72)

    if not results:
        print("Không tìm thấy dữ liệu phù hợp.")
        return

    for rank, result in enumerate(results, start=1):
        timestamp = format_timestamp(result.get("best_timestamp_seconds"))
        timestamp_text = f" | thời điểm: {timestamp}" if timestamp else ""
        print(
            f"{rank:02d}. score={result['score']:.4f} "
            f"| {result['media_type']} | {result['title']}"
            f"{timestamp_text}"
        )
        print(f"    {result['file_path']}")


def find_vlc() -> Optional[str]:
    possible_paths = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def open_result(result: Dict[str, Any]) -> None:
    file_path = str(result.get("file_path", ""))
    if not file_path or not os.path.exists(file_path):
        print(f"Không tìm thấy file: {file_path}")
        return

    media_type = result.get("media_type")
    timestamp = result.get("best_timestamp_seconds")

    try:
        if media_type == "video":
            vlc_path = find_vlc()
            if vlc_path:
                command = [vlc_path]
                if timestamp is not None:
                    command.append(f"--start-time={max(float(timestamp), 0.0):.3f}")
                command.append(file_path)
                subprocess.Popen(command)
                print(f"Đã mở video: {os.path.basename(file_path)}")
                if timestamp is not None:
                    print("Bắt đầu tại:", format_timestamp(float(timestamp)))
                return

        os.startfile(file_path)
        print(f"Đã mở file: {os.path.basename(file_path)}")

        if media_type == "video" and timestamp is not None:
            print("Không phát hiện VLC nên video mở từ đầu.")
            print("Thời điểm phù hợp nhất:", format_timestamp(float(timestamp)))

    except OSError as error:
        print(f"Không mở được file: {error}")


def choose_result(results: List[Dict[str, Any]]) -> None:
    if not results:
        return

    while True:
        choice = input(
            "\nNhập số thứ tự để mở file "
            "(Enter để tìm lại, 0 để thoát): "
        ).strip()

        if choice == "":
            return
        if choice == "0":
            raise SystemExit
        if not choice.isdigit():
            print("Vui lòng nhập một số hợp lệ.")
            continue

        selected_index = int(choice) - 1
        if selected_index < 0 or selected_index >= len(results):
            print(f"Vui lòng nhập số từ 1 đến {len(results)}.")
            continue

        open_result(results[selected_index])


def interactive_search(top_k: int) -> None:
    print_device_info()
    print("\nNhập nội dung cần tìm. Nhập 'exit' để thoát.")

    while True:
        try:
            query = input("\nTìm kiếm: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nĐã thoát.")
            break

        if query.lower() in {"exit", "quit", "thoat", "thoát"}:
            print("Đã thoát.")
            break
        if not query:
            print("Bạn chưa nhập nội dung.")
            continue

        try:
            results = search_media(query, top_k)
            print_results(query, results)
            choose_result(results)
        except SystemExit:
            print("Đã thoát.")
            break
        except Exception as error:
            print(f"Lỗi tìm kiếm: {error}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tìm kiếm ảnh/video bằng CLIP.")
    parser.add_argument("query", nargs="?", help='Ví dụ: "người mặc áo đỏ"')
    parser.add_argument("--top-k", type=int, default=10, help="Số kết quả trả về.")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    if args.query:
        print_device_info()
        results = search_media(args.query, args.top_k)
        print_results(args.query, results)
        choose_result(results)
    else:
        interactive_search(args.top_k)


if __name__ == "__main__":
    main()