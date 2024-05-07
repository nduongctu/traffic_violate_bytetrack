import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from violation import *

class VideoPlayer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Player")
        self.geometry("1920x1080")

        self.fps = None
        self.cap = None
        self.video_thread = None

        # Khung chứa video
        self.video_frame = tk.Frame(self, width=1420, height=980)
        self.video_frame.pack(side=tk.LEFT, anchor=tk.NW)

        # Nhãn hiển thị video
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack(expand=True, fill=tk.BOTH)

        # Khung chứa các nút bên phải video
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side=tk.RIGHT, anchor=tk.NE, padx=100, pady=30)

        # Các nút
        self.upload_button = tk.Button(self.button_frame, text="Tải lên video", command=self.open_file, width=15,height=2)
        self.upload_button.grid(row=0, column=1, pady=15, padx=100)

        self.play_button = tk.Button(self.button_frame, text="Play", command=self.play_video, width=15, height=2)
        self.play_button.grid(row=1, column=1, pady=15, padx=100)

        self.pause_button = tk.Button(self.button_frame, text="Pause", command=self.pause_video, state=tk.DISABLED,width=15, height=2)
        self.pause_button.grid(row=2, column=1, pady=15, padx=100)

        self.draw_line_button = tk.Button(self.button_frame, text="Vẽ đường thẳng", command=self.draw_line, width=15,height=2)
        self.draw_line_button.grid(row=3, column=1, pady=15, padx=100)

        self.process_button = tk.Button(self.button_frame, text="Xử lý", command=self.process, width=15, height=2)
        self.process_button.grid(row=4, column=1, pady=15, padx=100)

        # Bảng
        self.info_frame = tk.Frame(self)
        self.info_frame.pack(side=tk.RIGHT, padx=20)

        # Label trong bảng thông tin
        self.info_label = tk.Label(self.button_frame, text="Thông tin vi phạm:")
        self.info_label.grid(row=5, column=1, pady=10)

        # Listbox để hiển thị danh sách thông tin vi phạm
        self.info_listbox = tk.Listbox(self.button_frame, width=40, height=10)
        self.info_listbox.grid(row=6, column=1, pady=10)

        # Label mức phạt
        self.info_label = tk.Label(self.button_frame, text="Thông tin mức phạt:")
        self.info_label.grid(row=7, column=1, pady=10)

        # Khung text hiển thị thông tin mức phạt
        self.info_text_penalty = tk.Text(self.button_frame, width=40, height=10)
        self.info_text_penalty.grid(row=8, column=1, pady=10)

        self.video_path = None
        self.video_thread = None
        self.line_start = None
        self.line_end = None
        self.is_video_playing = False

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", ".mp4;.avi;*.mov")])
        if file_path:
            self.video_path = file_path
            self.is_video_playing = False
            self.update_video_label()

            # Lấy giá trị fps từ đối tượng cv2.VideoCapture
            cap = cv2.VideoCapture(file_path)
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

    def play_video(self):
        if self.video_path and not self.is_video_playing:
            self.is_video_playing = True
            self.play_button.configure(state=tk.DISABLED)
            self.pause_button.configure(state=tk.NORMAL)
            self.cap = cv2.VideoCapture(self.video_path)

            # Lưu lại vị trí của các điểm bắt đầu và kết thúc của đường thẳng
            self.saved_line_start = self.line_start
            self.saved_line_end = self.line_end

            self.start_video()

    def start_video(self):
        if self.video_thread is None:
            self.video_thread = threading.Thread(target=self.update_video, daemon=True)
            self.video_thread.start()

    def pause_video(self):
        if self.is_video_playing:
            self.is_video_playing = False
            self.play_button.configure(state=tk.NORMAL)  # Enable the "Play" button
            self.pause_button.configure(state=tk.DISABLED)  # Disable the "Pause" button

    def stop_video(self):
        if self.video_thread is not None:
            self.is_video_playing = False
            self.video_thread.join()
            self.cap.release()
            self.video_thread = None

    def update_video(self):
        count_frame = 0
        while self.is_video_playing:
            ret, frame = self.cap.read()
            if not ret:
                self.is_video_playing = False
                self.play_button.configure(state=tk.NORMAL)
                self.pause_button.configure(state=tk.DISABLED)
                self.cap.release()
                break

            count_frame += 1
            second = count_frame / self.fps

            self.update_second_info(second)

            # Thay đổi kích thước khung hình video thành 1420x980
            frame = cv2.resize(frame, (1420, 980))

            if self.line_start is not None and self.line_end is not None:
                start = self.line_start
                end = self.line_end
                cv2.line(frame, start, end, (0, 0, 255), 2)

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_image)
            photo = ImageTk.PhotoImage(image)

            self.video_label.configure(image=photo)
            self.video_label.image = photo

    def draw_line(self):
        self.video_label.bind("<Button-1>", self.start_drawing_line)
        self.video_label.bind("<B1-Motion>", self.update_drawing_line)
        self.video_label.bind("<ButtonRelease-1>", self.finish_drawing_line)

    def start_drawing_line(self, event):
        self.line_start = (event.x, event.y)

    def update_drawing_line(self, event):
        self.line_end = (event.x, event.y)

    def finish_drawing_line(self, event):
        self.line_end = (event.x, event.y)
        self.video_label.unbind("<Button-1>")
        self.video_label.unbind("<B1-Motion>")
        self.video_label.unbind("<ButtonRelease-1>")
        self.update_video_label()

        # Lưu tọa độ đường thẳng vào file "toado.txt"
        with open("toado.txt", "w") as file:
            file.write(f"x1={self.line_start[0]},y1={self.line_start[1]}\n")
            file.write(f"x2={self.line_end[0]},y2={self.line_end[1]}")

    def update_violation_info(self, violation_info):
        self.info_listbox.insert(tk.END, violation_info)

    def update_penalty_info(self):
        if self.info_listbox.size() > 0:
            self.info_text_penalty.delete('1.0', tk.END)
            self.info_text_penalty.insert(tk.END,
         "Người điều khiển ô tô vi phạm lỗi vượt đèn đỏ và không tuân thủ các hiệu lệnh của người kiểm soát giao thông hay tín hiệu của đèn giao thông, mức phạt sẽ là từ 3.000.000 - 5.000.000 đồng. Đối với người điều khiển các loại phương tiện giao thông như xe máy chuyên dùng, mức phạt khi vượt đèn đỏ mức phạt sẽ là từ 2.000.000 - 3.000.000 đồng.")

    def process(self):
        if self.video_path:
            messagebox.showinfo("Thông báo", "Đang xử lý video. Vui lòng đợi trong khi quá trình hoàn thành.")
            processor = TrafficViolationProcessor(self.video_path)
            violations = processor.process()
            for violation in violations:
                self.update_violation_info(violation)
            messagebox.showinfo("Thông báo", "Quá trình xử lý đã hoàn thành.")
            self.video_path = 'output_video.avi'
            self.update_video_label()
            self.update_penalty_info()

            cap = cv2.VideoCapture(self.video_path)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                cv2.imshow('Output Video', frame)
                if cv2.waitKey(25) & 0xFF == ord('q'):  # Nhấn 'q' để thoát
                    break
            cap.release()
            cv2.destroyAllWindows()


    def update_second_info(self, second):
        self.info_label.config(text=f"Thông tin vi phạm:\nGiây: {second:.1f}")

    def update_info_list(self, violations):
        self.info_listbox.delete(0, tk.END)
        for violation in violations:
            self.info_listbox.insert(tk.END, violation)

    def update_video_label(self):
        if self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (1420, 980))
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
