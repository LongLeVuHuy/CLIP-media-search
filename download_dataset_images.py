from datasets import load_dataset
from pathlib import Path
import shutil

project_folder = Path(__file__).resolve().parent
output = project_folder / "input_media"
output.mkdir(exist_ok=True)

print("Đang tải dataset...")

dataset = load_dataset(
    "AminDehnavi/flickr30k",
    split="train",
)

number_of_images = min(100, len(dataset))

print(f"Đang lưu {number_of_images} ảnh...")

for index, item in enumerate(dataset.select(range(number_of_images))):
    image_path = output / f"image_{index:04d}.jpg"

    item["image"].convert("RGB").save(image_path)

    print(f"Đã lưu: {image_path.name}")

zip_base = project_folder / "clip_test_dataset"

shutil.make_archive(
    str(zip_base),
    "zip",
    root_dir=output,
)

print("\nHOÀN THÀNH")
print(f"Thư mục ảnh: {output}")
print(f"File ZIP: {zip_base}.zip")
