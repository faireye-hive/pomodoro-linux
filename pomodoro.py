import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QFont, QPen, QCursor, QRadialGradient

import qtawesome as qta
from PyQt6.QtCore import QSize, QUrl
import subprocess
import os

class PomodoroTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "POMODORO" # POMODORO, ALARM, BREAK
        self.sound_process = None
        self.blink_state = False
        
        self.initUI()
        self.initTimer()
        
        # Timer para o efeito de piscar
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink_effect)
        
        self.dragging = False
        self.offset = QPoint()

    def initUI(self):
        # Configurações da Janela
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(200, 200)

        # Layout Principal
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

        # Estilo da Fonte
        font_family = "Segoe UI"
        font_time = QFont(font_family, 32, QFont.Weight.Light)
        
        # Label do Tempo
        self.time_label = QLabel("25:00")
        self.time_label.setFont(font_time)
        self.time_label.setStyleSheet("color: #F0F0F0; background-color: transparent;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        # Layout Horizontal para os Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(btn_layout)

        # Estilo base para botões (sem texto, apenas icone)
        self.btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 15px;
                outline: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """

        # Botão Iniciar/Pausar
        self.start_btn = QPushButton()
        self.start_btn.setFixedSize(30, 30)
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.setToolTip("Iniciar/Pausar")
        self.start_btn.setStyleSheet(self.btn_style)
        
        # Ícones do Start/Pause
        self.icon_play = qta.icon('fa5s.play', color='white')
        self.icon_pause = qta.icon('fa5s.pause', color='white')
        self.icon_break = qta.icon('fa5s.coffee', color='white') # Icone para descanso
        
        self.start_btn.setIcon(self.icon_play)
        self.start_btn.setIconSize(QSize(12, 12)) 
        
        self.start_btn.clicked.connect(self.toggle_timer)
        btn_layout.addWidget(self.start_btn)

        # Botão Reset
        self.reset_btn = QPushButton()
        self.reset_btn.setFixedSize(30, 30)
        self.reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_btn.setToolTip("Resetar")
        self.reset_btn.setStyleSheet(self.btn_style)
        
        self.reset_btn.setIcon(qta.icon('fa5s.redo', color='white'))
        self.reset_btn.setIconSize(QSize(12, 12))
        
        self.reset_btn.clicked.connect(self.reset_timer)
        btn_layout.addWidget(self.reset_btn)

        # Botão Fechar
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setToolTip("Fechar")

        # Estilo específico para o hover do fechar (vermelho)
        close_style = self.btn_style + """
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 0.5);
            }
        """
        self.close_btn.setStyleSheet(close_style)
        
        self.close_btn.setIcon(qta.icon('fa5s.times', color='white')) 
        self.close_btn.setIconSize(QSize(14, 14))
        
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Área de desenho total
        rect = QRectF(0, 0, self.width(), self.height())
        gradient = QRadialGradient(rect.center(), rect.width()/2)
        
        # Cor Base
        if self.state == "ALARM" and self.blink_state:
            # Cor de Alarme (Vermelho Pulsante)
            color_center = QColor(200, 50, 50, 240)
            color_border = QColor(150, 20, 20, 200)
        elif self.state == "BREAK":
            # Cor de Descanso (Verde Calmo)
            color_center = QColor(40, 60, 40, 240)
            color_border = QColor(30, 50, 30, 220)
        else:
            # Cor Normal (Cinza/Preto)
            color_center = QColor(30, 30, 40, 240)
            color_border = QColor(30, 30, 40, 220)
            
        gradient.setColorAt(0.0, color_center) 
        gradient.setColorAt(0.7, color_border)
        gradient.setColorAt(1.0,  QColor(0, 0, 0, 0)) # Transparente total na borda

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)

    # Lógica do Clock
    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.remaining_time = 25 * 60 
        self.is_running = False

    def toggle_timer(self):
        if self.state == "ALARM":
            self.start_break()
            return
            
        if self.is_running:
            self.timer.stop()
            self.start_btn.setIcon(self.icon_play)
        else:
            self.timer.start(1000)
            self.start_btn.setIcon(self.icon_pause)
        self.is_running = not self.is_running

    def reset_timer(self):
        self.stop_alarm()
        self.timer.stop()
        self.blink_timer.stop()
        
        self.state = "POMODORO"
        self.remaining_time = 25 * 60
        self.is_running = False
        
        self.time_label.setStyleSheet("color: #F0F0F0; background-color: transparent;")
        self.update_display()
        self.start_btn.setIcon(self.icon_play)
        self.start_btn.setToolTip("Iniciar")
        self.update()

    def update_time(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_display()
        else:
            self.timer.stop()
            self.is_running = False
            
            if self.state == "POMODORO":
                self.trigger_alarm()
            elif self.state == "BREAK":
                self.reset_timer() # Volta pro inicio do pomodoro

    def trigger_alarm(self):
        self.state = "ALARM"
        self.blink_state = True
        self.blink_timer.start(500) # Pisca a cada 500ms
        self.start_btn.setIcon(self.icon_break) # Vira botão de café
        self.start_btn.setToolTip("Iniciar Descanso")
        self.time_label.setText("00:00")
        self.play_sound()
        
    def start_break(self):
        self.stop_alarm()
        self.state = "BREAK"
        self.remaining_time = 2 * 60 # 2 Minutos de Descanso
        self.blink_timer.stop()
        self.update() # Força repaint para cor verde
        
        self.timer.start(1000)
        self.is_running = True
        self.start_btn.setIcon(self.icon_pause)
        self.update_display()

    def play_sound(self):
        # Tenta tocar alarm.wav usando play de sistema
        sound_file = os.path.join(os.getcwd(), "alarm.wav")
        if os.path.exists(sound_file):
            try:
                # Tenta paplay (PulseAudio) ou aplay (ALSA)
                player = 'paplay' if os.path.exists('/usr/bin/paplay') else 'aplay'
                self.sound_process = subprocess.Popen([player, sound_file])
            except:
                pass # Falha silenciosa se não conseguir tocar

    def stop_alarm(self):
        if self.sound_process:
            self.sound_process.terminate()
            self.sound_process = None
        self.blink_state = False

    def blink_effect(self):
        self.blink_state = not self.blink_state
        self.update() # trigger paintEvent

    def update_display(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.time_label.setText(f"{minutes:02}:{seconds:02}")

    # Lógica de Arrastar Janela
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.close()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def closeEvent(self, event):
        self.stop_alarm()
        if self.timer.isActive():
            self.timer.stop()
        QApplication.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomodoroTimer()
    window.show()
    sys.exit(app.exec())



