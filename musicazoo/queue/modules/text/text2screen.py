import Tkinter

def splash(fsg,text,bg="black",fg="white",font="Helvetica",size=72):
    c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,bg=bg)
    c.pack()

    coord = fsg.center()
    arc = c.create_text(coord, text=text, fill=fg, justify=Tkinter.CENTER, font=(font,size))
