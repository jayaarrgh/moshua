# custom pyinstaller --add-data options to make sure we  we get everything we need
# I don't remember why I need empty.txt to get import yaspin's spinners, but it worked
moshua:
	pyinstaller --add-data venv/lib/python3.6/site-packages/yaspin/data/spinners.json:yaspin/data --add-data empty.txt:spinners --onefile datamosh_gui.py
