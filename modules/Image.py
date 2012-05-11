from musicazooTemplates import MusicazooShellCommandModule

class Image(MusicazooShellCommandModule):
    resources = ("screen",)
    persistent = True
    keywords = ("image", "img")
    command = ("image",)
    title = "Image"
