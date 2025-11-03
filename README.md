WITAM WSZYSTKICH ZGROMADZONYCH
By odpalić aplikację proszę o wykonanie następoujących kroków.
1. Najpierw pobierz wymagane zależności:
W terminalu wpisz:

cd backend
pip install -r requirements.txt

2. Gdy zależności zostały pobrane, (mam nadzieje ze o niczym nie zapomniałąm i w tym pliku requirements.txt są wszystkie wymagane) to będąc dalej w folderze backend wpisz:

uvicorn main:app --reload

3. Powinien wygenerowac się link, klikij go (Ctrl+click) i powinna sie otworzyc strona w internecie
