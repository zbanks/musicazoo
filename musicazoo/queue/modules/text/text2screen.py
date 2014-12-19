import Tkinter
import musicazoo.settings as sets

def splash(fsg,text,bg=sets.bg_color,fg=sets.fg_color,font="Helvetica",size=72):
    c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,bg=bg)
    c.pack()

    coord = fsg.center()
    arc = c.create_text(coord, text=text, fill=fg, justify=Tkinter.CENTER, font=(font,size))

def paragraph(fsg,text,bg=sets.bg_color,fg=sets.fg_color,font="Mono",size=32,padx=10,pady=10):
    #c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,bg=bg)
    #c.pack()

    fsg.config(bg=bg)

    textbox = Tkinter.Text(fsg,
                           font=(font, size),
                           wrap=Tkinter.WORD,
                           highlightthickness=0,
                           relief=Tkinter.FLAT,
                           fg=fg,
                           bg=bg,
                          )
    textbox.insert(Tkinter.END, text)
    textbox.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, padx=padx, pady=pady)

def email(fsg,text,bg=sets.bg_color,fg=sets.fg_color,font="Arial",sender_size=36,subject_size=48,body_size=32,padx=10,pady=0):
    sender = text['sender']
    subject = text['subject']
    body = text['body']

    #fsg.beginning_dead_time=18
    #fsg.end_dead_time=-3

    fsg.configure(bg=bg)

    widget_from = Tkinter.Label(fsg, 
                                font=(font, sender_size), 
                                wraplength=fsg.width,
                                text=sender,
                                fg=fg,
                                bg=bg,
                               )
    widget_from.pack(padx=padx,pady=pady)
    widget_subj = Tkinter.Label(fsg, 
                                font=(font,subject_size), 
                                wraplength=fsg.width,
                                text=subject,
                                fg=fg,
                                bg=bg,
                               )
    widget_subj.pack(padx=padx,pady=pady)

    widget_body = Tkinter.Text(fsg,
                               font=(font,body_size),
                               wrap=Tkinter.WORD,
                               highlightthickness=0,
                               relief=Tkinter.FLAT,
                               fg=fg,
                               bg=bg,
                              )

    widget_body.insert(Tkinter.END, body)
    widget_body.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, padx=padx, pady=pady)
