import os
import time
import utils
import datetime
import tkinter as tk
import tkmacosx as tkm
from tkinter.font import Font


class AppFunctions:

    # Threading improves smoothness and overall UI.
    # GUI lags out when image is downloaded in the
    # same thread.
    @utils.threaded
    def change_wallpaper(self):
        while self.b2['state'] != 'disabled':
            print('going on', self.focus_get(), self._sleep_time)
            with utils.download_image(self.imageslink.download_link(True), True) as img:
                utils.change_background_image(img.filename)
                # Deleting the image is not working so this is
                # the workaround which will delete the previous
                # image when new one is downloaded and set.
                img.delete_previous()
            if self.focus_get() is not None:
                self.change_time.reset()
                self._sleep_time = self.change_time.get()
                self.timer_label.timer(self.change_time.get())
            time.sleep(self._sleep_time)

    def button_click(self, button):
        if button['text'] == 'Resume':
            button['state'] = 'disabled'
            self.b2['state'] = 'normal'
            self.timer_label.timer(self.change_time.get())
            self.after(self.change_time.get()*1000, self.change_wallpaper)
        else:
            self.after_cancel(self._after_id.get('timer', ' '))
            self.timer_label.config(text='Paused')
            button['state'] = 'disabled'
            self.b1['state'] = 'normal'

    def change_categories(self, *args):
        new_categories = dict(**self.imageslink.categories)
        for wid in self.setting_containter.winfo_children():
            if isinstance(wid, tk.Checkbutton) and not wid.var.get():
                del new_categories[wid['text']]
        print(new_categories)
        # self.imageslink.categories = new_categories
        # issue not working properly


class AppLayouts:

    def heading_layout(self, **kw):
        font = self.heading_font.copy()
        font.config(size=font['size']+20, weight='bold')
        self.heading_lb = tk.Label(
            self, text='Auto Background', fg=self.fg, bg=self.bg,
            font=font, pady=10)
        self.heading_lb.grid(**kw)

    def button_layout(self, **kw):
        self.button_containter = tk.LabelFrame(
            self, text='Actions', fg=self.fg, bg=self.bg, labelanchor='n',
            font=self.heading_font)
        self.button_containter.grid(**kw)
        self.button_containter.rowconfigure(0, weight=1)
        self.button_containter.columnconfigure(0, weight=1)
        self.button_containter.columnconfigure(1, weight=1)

        self.b1 = tkm.Button(
            self.button_containter, text='Resume', fg=self.fg, bg=self.bg_but,
            borderless=1, pady=10, font=self.body_font, focuscolor=self.fg,
            activebackground=(self.bg_but.get(), self.bg.get()),
            disabledbackground='#FEFAEC', disabledforeground='grey')
        self.b1['command'] = lambda: self.button_click(self.b1)
        self.b1.grid(row=0, column=0, padx=5, sticky='ew', pady=5)
        self.b2 = tkm.Button(
            self.button_containter, text='Pause', fg=self.fg, bg=self.bg_but,
            borderless=1, pady=10, font=self.body_font, focuscolor=self.fg,
            activebackground=self.bg,
            disabledbackground='#FEFAEC', disabledforeground='grey')
        self.b2['command'] = lambda: self.button_click(self.b2)
        self.b2.grid(row=0, column=1, padx=(0, 5), sticky='ew', pady=5)

    def setting_layout(self, **kw):
        self.setting_containter = tk.LabelFrame(
            self, text='Settings', fg=self.fg, bg=self.bg, labelanchor='n',
            font=self.heading_font)
        self.setting_containter.grid(**kw)

        spinbox_container = tk.Frame(self.setting_containter, bg=self.bg)
        spinbox_container.grid(row=0, columnspan=2, padx=5, pady=10)
        tk.Label(
            spinbox_container, text='Change in', fg=self.fg, bg=self.bg,
            font=self.body_font).grid(row=0, column=0, padx=5)

        self.change_time = tk.IntVar()

        def time_seconds(*a):
            time = 0
            d = {n: w for n, w in spinbox_container.
                 children.items() if isinstance(w, tk.Spinbox)}
            for i in ('d', 'h', 'm', 's'):
                if i == 'd':
                    time += d['!spinbox'].var.get() * 86400
                elif i == 'h':
                    time += d['!spinbox2'].var.get() * 3600
                elif i == 'm':
                    time += d['!spinbox3'].var.get() * 60
                else:
                    time += d['!spinbox4'].var.get()
            self.change_time.set(time)
            self._sleep_time = time

        self.change_time.reset = time_seconds

        for c in range(1, 5):
            c *= 2
            sp = tk.Spinbox(
                spinbox_container, from_=0, to=59, fg=self.fg, width=5, bg=self.bg_but,
                highlightbackground=self.bg, highlightcolor=self.fg,
                justify='center', font=self.body_font)
            sp.var = sp['textvariable'] = tk.IntVar()
            if c == 6:
                sp.var.set(5)
            sp.grid(row=0, column=c)
            if c < 7:
                tk.Label(
                    spinbox_container, text=':', fg=self.fg, bg=self.bg,
                    font=('', 20)).grid(row=0, column=c+1, padx=(5, 0), pady=(0, 5))
            sp.var.trace_add('write', time_seconds)

        time_seconds()
        tk.Label(
            self.setting_containter, text='-'*10+' Categories '+'-'*10, fg=self.fg,
            bg=self.bg, font=self.heading_font).grid(
                row=1, columnspan=2, padx=5, pady=(15, 5))

        row = 2
        for count, cate in enumerate(self.imageslink.categories.keys()):
            ckb = tk.Checkbutton(
                self.setting_containter, text=cate, fg=self.fg, bg=self.bg,
                font=self.body_font)
            ckb.var = ckb['variable'] = tk.BooleanVar(
                self.setting_containter, value=0)
            ckb.var.trace_add('write', self.change_categories)
            if 'macbook' in cate.lower():
                ckb.var.set(1)
            if count % 2 == 0:
                ckb.grid(row=row, column=0, sticky='w', padx=5)
            else:
                ckb.grid(row=row, column=1, sticky='w', padx=5)
                row += 1

    def preview_layout(self, **kw):
        pass

    def timer_layout(self, **kw):
        self.timer_label = tk.Label(
            self, fg=self.fg, bg=self.bg, font=self.body_font)
        self.timer_label.grid(**kw)

        def timer(seconds):
            time = datetime.timedelta(seconds=seconds)
            self.timer_label['text'] = f'Next wallpaper in: {time}'
            if seconds:
                self.change_time.set(self.change_time.get() - 1)
                self._after_id['timer'] = self.after(
                    1000, timer, seconds - 1)
        self.timer_label.timer = timer


class App(tk.Tk, AppLayouts, AppFunctions):
    def __init__(self):
        super().__init__()
        self.title('Auto Background')
        self.resizable(0, 0)
        self._after_id = {}
        self.bg = tkm.ColorVar(self, value='#2EB872')
        self.fg = tkm.ColorVar(self, value='#EEFFE4')
        self.bg_but = tkm.ColorVar(self, value='#A3DE83')
        self.heading_font = Font(family='SignPainter', size=17)
        self.body_font = Font(family='DIM Condensed', size=11)
        self['bg'] = self.bg

        self.imageslink = utils.ImageLink(pages=20)

        self.heading_layout(row=0, column=0, padx=5, pady=10, sticky='nsew')
        self.button_layout(row=1, column=0, padx=5, pady=10, sticky='ew')
        self.timer_layout(row=2, column=0, padx=5, pady=10, sticky='nsew')
        self.setting_layout(row=3, column=0, padx=5, pady=10, sticky='ew')


app = App()
app.mainloop()
