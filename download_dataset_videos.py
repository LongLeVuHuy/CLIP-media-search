from pathlib import Path
import shutil

from huggingface_hub import HfApi, hf_hub_download


REPO_ID = "HumynLabs/Street-videos"
NUMBER_OF_VIDEOS = 50

project_folder = Path(__file__).resolve().parent
output_folder = project_folder / "input_media"
output_folder.mkdir(parents=True, exist_ok=True)

api = HfApi()

print("Đang lấy danh sách file...")

all_files = api.list_repo_files(
    repo_id=REPO_ID,
    repo_type="dataset",
)

video_files = [
    file_name
    for file_name in all_files
    if file_name.lower().endswith(
        (".mp4", ".avi", ".mov", ".mkv")
    )
]

print(f"Tìm thấy {len(video_files)} video.")

selected_files = video_files[:NUMBER_OF_VIDEOS]

if not selected_files:
    raise RuntimeError("Không tìm thấy video trong dataset.")

for index, repo_file in enumerate(selected_files, start=1):
    print(f"[{index}/{len(selected_files)}] Đang tải {repo_file}")

    cached_file = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=repo_file,
    )

    extension = Path(repo_file).suffix.lower()
    destination = output_folder / f"video_{index:03d}{extension}"

    shutil.copy2(cached_file, destination)

print("\nHOÀN THÀNH")
print(f"Video nằm tại: {output_folder}")