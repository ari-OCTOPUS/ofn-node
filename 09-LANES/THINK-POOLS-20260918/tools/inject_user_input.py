"""Inject ONE real input event (mouse move via SendInput) — for the item-8
preemption demonstration. Indistinguishable from the user at the OS level:
GetLastInputInfo resets exactly as it does for a human touch."""
import ctypes

PUL = ctypes.POINTER(ctypes.c_ulong)


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]


move = INPUT(type=0, mi=MOUSEINPUT(1, 1, 0, 1, 0, None))  # MOUSEEVENTF_MOVE
n = ctypes.windll.user32.SendInput(1, ctypes.byref(move), ctypes.sizeof(INPUT))
print("injected_events=", n)
