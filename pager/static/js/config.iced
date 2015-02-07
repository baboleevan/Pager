c = 
  default_message_color: 0xFFFFFF
  default_message: 'New pager is opened "Pager is slow but, warm enough to move your heart."'
  platform: navigator.platform.toLowerCase()
  message_colors: [
    # normal , 30% opacity
    [0x63dbf0, 0xd0f4fa]
    [0xf9ef7c, 0xfdfad7]
    [0xf2a6a6, 0xfbe4e4]
    [0xa9d97e, 0xe5f4d8]
    [0xb8b8b8, 0xeaeaea]
    [0xfff, 0xfff]
  ]
  raven: 'https://75ba3f2bdcda40078c693a1ad19365e7:5f5e9a1777e84576976a83913bd7c0f8@app.getsentry.com/6224'

c.is_ios = navigator.platform.toLowerCase() in ['iphone', 'ipad']
c.prevent_user_selection = c.is_ios
c.installable = c.is_ios
c.installed = window.navigator.standalone

c.message_colors.darken = {}
for [dark, light] in c.message_colors
  c.message_colors.darken[light] = dark

module.exports = c
