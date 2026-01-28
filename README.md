#  Prediction App – Aplikacja do przewidywania wyników meczów

##  Opis projektu

Prediction App to aplikacja webowa służąca do statystycznego przewidywania wyników meczów piłkarskich na podstawie danych historycznych. Model analizuje **5 ostatnich spotkań** obu drużyn i na tej podstawie wylicza najbardziej prawdopodobny wynik meczu.

Projekt ma charakter edukacyjno-analityczny – nie jest to system oparty na AI/ML, lecz na prostych i przejrzystych metodach statystycznych, dzięki czemu łatwo zrozumieć jego działanie i dalej go rozwijać.


##  Jak działa przewidywanie meczów?

1. Użytkownik wybiera drużynę gospodarzy i gości
2. Backend pobiera dane o 5 ostatnich meczach każdej drużyny
3. Dla każdej drużyny obliczane są:

   -średnia liczba strzelonych bramek
   -średnia liczba straconych bramek
4. Na podstawie tych średnich wyliczany jest:

   - przewidywany wynik meczu
   - prawdopodobieństwo wygranej / remisu / porażki
5. Wynik jest prezentowany w czytelnej formie w interfejsie użytkownika


## Backend (Python / Flask)

`app.py`

Backend odpowiada za:

- pobieranie danych meczowych
- przetwarzanie statystyk drużyn
- obliczanie predykcji
- udostępnianie API dla frontendu

API zwraca dane w formacie JSON, np.:

- przewidywany wynik
- średnie bramki
- procentowe szanse

##  Frontend (React + Vite)

`App.jsx`

- główny komponent aplikacji
- zarządza routingiem i strukturą strony

`HomePredict.jsx`

- główny widok predykcji
- formularz wyboru drużyn
- wysyłanie zapytania do backendu
- wyświetlanie wyników predykcji