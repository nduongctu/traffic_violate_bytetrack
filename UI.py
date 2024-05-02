import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk
import threading

class VideoPlayer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Player")
        self.geometry("1920x1080")

        # Khung chứa video
        self.video_frame = tk.Frame(self, width=1420, height=980)
        self.video_frame.pack(side=tk.LEFT, anchor=tk.NW)

        # Nhãn hiển thị video
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack(expand=True, fill=tk.BOTH)  # Đặt fill và expand để lấp đầy toàn bộ không gian

        # Khung chứa các nút bên phải video
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side=tk.RIGHT, anchor=tk.NE, padx=100, pady=30)

        # Nút tải lên video
        self.upload_button = tk.Button(self.button_frame, text="Tải lên video", command=self.open_file, width=15, height=2)
        self.upload_button.pack(pady=15, padx=100)

        # Nút phát video
        self.play_button = tk.Button(self.button_frame, text="Play", command=self.play_video, width=15, height=2)
        self.play_button.pack(pady=15, padx=100)

        # Nút dừng video
        self.pause_button = tk.Button(self.button_frame, text="Pause", command=self.pause_video, state=tk.DISABLED, width=15, height=2)
        self.pause_button.pack(pady=15, padx=100)

        # Nút vẽ đường thẳng
        self.draw_line_button = tk.Button(self.button_frame, text="Vẽ đường thẳng", command=self.draw_line, width=15, height=2)
        self.draw_line_button.pack(pady=15, padx=100)

        # Nút xử lý
        self.process_button = tk.Button(self.button_frame, text="Xử lý", command=self.process, width=15, height=2)
        self.process_button.pack(pady=15, padx=100)

        self.video_path = None
        self.video_thread = None
        self.line_start = None
        self.line_end = None
        self.is_video_playing = False  # Biến trạng thái để kiểm soát việc phát video

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", ".mp4;.avi;*.mov")])
        if file_path:
            self.video_path = file_path
            self.is_video_playing = False  # Đặt biến trạng thái thành False khi tải video
            self.update_video_label()  # Hiển thị video đã tải lên

    def play_video(self):
        if self.video_path and not self.is_video_playing:
            self.is_video_playing = True
            self.play_button.configure(state=tk.DISABLED)  # Vô hiệu hóa nút Play
            self.pause_button.configure(state=tk.NORMAL)  # Kích hoạt nút Pause
            self.start_video()

    def pause_video(self):
        if self.is_video_playing:
            self.is_video_playing = False
            self.play_button.configure(state=tk.NORMAL)  # Kích hoạt nút Play
            self.pause_button.configure(state=tk.DISABLED)  # Vô hiệu hóa nút Pause

    def start_video(self):
        if self.video_thread is not None:
            self.stop_video()

        self.video_thread = threading.Thread(target=self.update_video, args=(), daemon=True)
        self.video_thread.start()

    def update_video(self):
        cap = cv2.VideoCapture(self.video_path)
        while True:
            if not self.is_video_playing:  # Kiểm tra xem có phải video đang phát hay không
                break

            ret, frame = cap.read()
            if not ret:
                break

            # Resize frame
            frame = cv2.resize(frame, (1420, 980))

            # Vẽ đường thẳng nếu đã được xác định
            if self.line_start is not None and self.line_end is not None:
                cv2.line(frame, self.line_start, self.line_end, (0, 0, 255), 2)

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_image)
            photo = ImageTk.PhotoImage(image)

            self.video_label.configure(image=photo)
            self.video_label.image = photo
            self.video_label.update()

        cap.release()

    def stop_video(self):
        if self.video_thread is not None:
            self.is_video_playing = False  # Đặt biến trạng thái thành False để dừng video
            self.video_thread.join()
            self.video_thread = None

    def draw_line(self):
        # Bắt đầu vẽ đường thẳng khi nút "Vẽ đường thẳng" được bấm
        self.video_label.bind("<Button-1>", self.start_drawing_line)
        self.video_label.bind("<B1-Motion>", self.update_drawing_line)
        self.video_label.bind("<ButtonRelease-1>", self.finish_drawing_line)

    def start_drawing_line(self, event):
        # Lưu tọa độ điểm bắt đầu vẽ đường thẳng
        self.line_start = (event.x, event.y)

    def update_drawing_line(self, event):
        # Cập nhật tọa độ điểm kết thúc vẽ đường thẳng
        self.line_end = (event.x, event.y)

    def finish_drawing_line(self, event):
        # Kết thúc vẽ đường thẳng
        self.line_end = (event.x, event.y)
        self.video_label.unbind("<Button-1>")
        self.video_label.unbind("<B1-Motion>")
        self.video_label.unbind("<ButtonRelease-1>")
        self.update_video_label()  # Hiển thị video đã vẽ đường thẳng
        with open('toado.txt', 'w') as file:
            file.write(f'x1={self.line_start[0]},y1={self.line_start[1]}\n')
            file.write(f'x2={self.line_end[0]},y2={self.line_end[1]}')

    def process(self):
        pass  # Hàm xử lý khi bấm nút "Xử lý"

    def update_video_label(self):
        if self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            if ret:
                # Resize frame
                frame = cv2.resize(frame, (1420, 980))

                # Vẽ đường thẳng nếu đã được xác định
                if self.line_start is not None and self.line_end is not None:
                    cv2.line(frame, self.line_start, self.line_end, (0, 0, 255), 2)

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb_image)
                photo = ImageTk.PhotoImage(image)
                self.video_label.configure(image=photo)
                self.video_label.image = photo
            cap.release()

if __name__ == "__main__":
    app = VideoPlayer()
    app.mainloop()