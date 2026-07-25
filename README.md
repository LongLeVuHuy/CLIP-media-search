# CLIP Image and Video Search

Ứng dụng tìm kiếm ảnh và video bằng câu mô tả tiếng Việt hoặc tiếng Anh.

Hệ thống sử dụng CLIP để chuyển ảnh, video và câu truy vấn thành vector, sau đó so sánh độ tương đồng để trả về các kết quả phù hợp nhất.

## Chức năng

- Tải ảnh mẫu từ Flickr30k.
- Tải video mẫu từ Hugging Face.
- Chuyển ảnh thành vector CLIP.
- Trích xuất khung hình từ video và tạo vector CLIP.
- Lưu dữ liệu vector vào `media_clip.json`.
- Tìm kiếm ảnh và video bằng văn bản.
- Xác định thời điểm phù hợp nhất trong video.
- Hiển thị kết quả trên giao diện web chạy local.
- Hỗ trợ phát video trực tiếp trên trình duyệt.

## Công nghệ sử dụng

- Python
- FastAPI
- Uvicorn
- HTML, CSS, JavaScript
- PyTorch
- Sentence Transformers
- CLIP
- OpenCV
- Pillow

## Cấu trúc thư mục

```text
project/
├── app.py
├── media_manager.py
├── search_media.py
├── download_dataset_images.py
├── download_dataset_videos.py
├── requirements.txt
├── README.md
├── .gitignore
├── media_clip.json
│
├── input_media/
│   └── .gitkeep
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── app.js
```

## Yêu cầu hệ thống

- Python 3.10 hoặc Python 3.11.
- Windows 10 hoặc Windows 11.
- Kết nối Internet trong lần đầu tải model và thư viện.
- Có thể chạy bằng CPU; GPU NVIDIA có CUDA sẽ nhanh hơn.

## Tải mã nguồn

```powershell
git clone LINK_REPOSITORY
cd TEN_THU_MUC_REPOSITORY
```

Ví dụ:

```powershell
git clone https://github.com/username/clip-media-search.git
cd clip-media-search
```

## Tạo môi trường ảo

```powershell
python -m venv .venv
```

Kích hoạt bằng PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Hoặc bằng Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

## Cài đặt thư viện

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Chuẩn bị dữ liệu

### Cách 1: Chép dữ liệu thủ công

Chép ảnh và video vào thư mục:

```text
input_media
```

Định dạng ảnh hỗ trợ:

```text
.jpg, .jpeg, .png, .webp, .bmp
```

Định dạng video hỗ trợ:

```text
.mp4, .avi, .mkv, .mov, .wmv
```

### Cách 2: Tải ảnh mẫu

```powershell
python download_dataset_images.py
```

### Cách 3: Tải video mẫu

```powershell
python download_dataset_videos.py
```

Ảnh và video tải về sẽ được lưu trong `input_media`.

## Tạo cơ sở dữ liệu vector

Sau khi đã có dữ liệu trong `input_media`, chạy:

```powershell
python media_manager.py --scan-once
```

Chương trình sẽ:

1. Quét toàn bộ ảnh và video.
2. Tạo embedding CLIP.
3. Trích xuất frame từ video.
4. Lưu dữ liệu vào `media_clip.json`.
5. Bỏ qua các file đã được lập chỉ mục trước đó.

## Lập chỉ mục lại toàn bộ

```powershell
python media_manager.py --reindex
```

## Theo dõi thư mục tự động

```powershell
python media_manager.py
```

Nhấn `Ctrl + C` để dừng.

## Tìm kiếm bằng Command Prompt

Chạy chế độ nhập truy vấn liên tục:

```powershell
python search_media.py
```

Tìm trực tiếp bằng một lệnh:

```powershell
python search_media.py "người đang đi xe đạp trên đường"
```

Chỉ định số lượng kết quả:

```powershell
python search_media.py "một chiếc ô tô màu đỏ" --top-k 5
```

## Chạy giao diện web local

Khởi động web:

```powershell
python -m uvicorn app:app --reload
```

Khi Terminal hiển thị:

```text
Application startup complete.
```

mở trình duyệt tại:

```text
http://127.0.0.1:8000
```

Không đóng cửa sổ Terminal trong khi web đang chạy. Nhấn `Ctrl + C` để dừng server.

## Cách sử dụng giao diện web

1. Nhập câu mô tả vào ô tìm kiếm.
2. Chọn số lượng kết quả.
3. Nhấn nút **Tìm kiếm**.
4. Ảnh và video phù hợp nhất sẽ hiển thị bên phải.
5. Video hiển thị thời điểm có nội dung phù hợp nhất.
6. Có thể phát video trực tiếp trên trình duyệt.

## Khi thêm dữ liệu mới

Sau khi thêm ảnh hoặc video mới vào `input_media`, chạy lại:

```powershell
python media_manager.py --scan-once
```

Sau đó tải lại trang web.


## Một số lỗi thường gặp

### Không tìm thấy FastAPI

```powershell
python -m pip install fastapi uvicorn
```

### Không tìm thấy Jinja2

```powershell
python -m pip install jinja2
```

### Lỗi `Attribute "app" not found in module "app"`

Trong `app.py` phải có:

```python
from fastapi import FastAPI

app = FastAPI()
```

### Web không hiện kết quả

Chạy:

```powershell
python media_manager.py --scan-once
```

và kiểm tra file `media_clip.json` đã được tạo.

### Web không mở được

Mở đúng địa chỉ:

```text
http://127.0.0.1:8000
```

Không dùng `https://127.0.0.1:8000`.

## Ghi chú

- Lần chạy đầu có thể mất thời gian vì chương trình phải tải model CLIP.
- Video càng dài thì thời gian lập chỉ mục càng lâu.
- Chất lượng tìm kiếm phụ thuộc vào dữ liệu đầu vào và câu truy vấn.
- Không nên tải `.venv`, dữ liệu ảnh/video và file vector lớn lên GitHub.
