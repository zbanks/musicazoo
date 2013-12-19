NAME = "Musicazoo"
LOCATION = "Glounge"
COLORS={'bg':'#406873','fg':'#F3FDE1'}

import musicazoo.backgrounds.image
import musicazoo.backgrounds.logo

import musicazoo.modules.netvid
import musicazoo.modules.text
import musicazoo.modules.youtube

import musicazoo.statics.identity
import musicazoo.statics.volume

MODULES = [
    musicazoo.modules.youtube.Youtube,
    musicazoo.modules.text.Text,
    musicazoo.modules.netvid.NetVid
]

STATICS = [
    musicazoo.statics.volume.Volume(),
    musicazoo.statics.identity.Identity(name=NAME, location=LOCATION, colors=COLORS)
]

BACKGROUNDS = [
    musicazoo.backgrounds.logo.Logo,
    musicazoo.backgrounds.image.ImageBG
]
