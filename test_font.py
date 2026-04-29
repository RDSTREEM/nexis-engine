from imgui_bundle import imgui

imgui.create_context()
io = imgui.get_io()
fonts = io.fonts

# Add default font
font_cfg = imgui.ImFontConfig()
fonts.add_font_default(font_cfg)

# Check for Build method
print("Looking for Build method:")
for m in dir(fonts):
    if "build" in m.lower() or "get_tex" in m.lower():
        print(f"  {m}")

# Try calling Build if it exists
if hasattr(fonts, "Build"):
    print("\nCalling fonts.Build()...")
    fonts.Build()
    print("After Build, tex_is_built:", fonts.tex_is_built)

# Check for GetTexDataAs methods
print("\nLooking for GetTexData methods:")
for m in dir(fonts):
    if "GetTexData" in m:
        print(f"  {m}")
