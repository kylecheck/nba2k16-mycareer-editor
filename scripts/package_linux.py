"""Create the clean Linux download from the repository sources."""
import pathlib,zipfile
root=pathlib.Path(__file__).resolve().parents[1]
files=['app.py','backend.py','process_memory.py','themed_ui.py','ui_values.py','native_x11.py','fields.json','build.json','Launch.sh','README.md','LICENSE']
(root/'dist').mkdir(exist_ok=True)
with zipfile.ZipFile(root/'dist/NBA2K16-Linux.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(root/name,'NBA2K16-MyCareer-Editor/'+name)
print('dist/NBA2K16-Linux.zip')
