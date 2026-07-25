# CLIP Image and Video Search

Chương trình tìm kiếm ảnh và video bằng câu mô tả tiếng Việt.

## Chức năng

- Tải ảnh mẫu từ Flickr30k.
- Tải video mẫu từ Hugging Face.
- Chuyển ảnh và video thành vector CLIP.
- Lưu vector vào `media_clip.json`.
- Tìm kiếm ảnh/video bằng văn bản.
- Tìm thời điểm phù hợp nhất trong video.

## Cài đặt

Yêu cầu Python 3.10 hoặc Python 3.11.

```powershell

git clone LINK_REPOSITORY
cd "LINK_REPOSITORY"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

## Chuẩn bị dữ lệu
- Chép dữ liệu vào file input_media bằng cách: 
	+ Tải ảnh chạy bằng cmd: python download_dataset_images.py
	+ Tải videos chạy bằng cmd: python download_dataset_videos.py
- Tạo cơ sở dữ liệu vector ( xử lý hình ảnh )
	+ python media_manager.py

## Tìm kiếm hình ảnh bằng văn bản
- python search_media.py