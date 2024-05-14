# Codebook

This is the code book that describes the variables and the data collected.

* [The data](#data)
* [The variables in the raw file](#variables_raw)
* [The variables in the cleaned file](#variables_clean)

<h1 id=data>The data</h1>

The data collected was obtained by scraping the webpage [www.mtgtop8.com](https://www.mtgtop8.com/) on the 14/05/2024. The result is stored in the csv file called `raw_magic.csv`.

<h1 id=variables_raw>The variables in `raw_magic.csv`</h1>

<table>
  <tr><td valign=top>Deck</td><td>The name of the deck.</td></tr>
  <tr><td valign=top>Player</td><td>The name of the player.</td></tr>
  <tr><td valign=top>Format</td><td>The format of the competition (always 'standard').</td></tr>
  <tr><td valign=top>Event</td><td>The event in which the deck was played.</td></tr>
  <tr><td valign=top>Level</td><td>The level of the competition (always NaN).</td></tr>
  <tr><td valign=top>Rank</td><td>The ranking of the deck.</td></tr>
  <tr><td valign=top>Date</td><td>The date of the event.</td></tr>
  <tr><td valign=top>LANDS</td><td>The number of Lands in the deck.</td></tr>
  <tr><td valign=top>CREATURES</td><td>The number of Creatures in the deck.</td></tr>
  <tr><td valign=top>INSTANTS_nad_SORC.</td><td>The number of Instants and Sorceries in the deck.</td></tr>
  <tr><td valign=top>OTHER_SPELLS</td><td>The number of Other Spells in the deck.</td></tr>
  <tr><td valign=top>SIDEBOARD</td><td>The size of the sideboard (always 0.0).</td></tr>
  <tr><td valign=top>LANDS_(NN)</td><td>The number of Lands in the deck when it contained also double-face cards which can be Lands (the number in parentheses is the total number of lands counting also these cards).</td></tr>
</table>

<h1 id=variables_clean>The variables in `magic.csv`</h1>

<table>
  <tr><td valign=top>Deck</td><td>The name of the deck.</td></tr>
  <tr><td valign=top>Player</td><td>The name of the player.</td></tr>
  <tr><td valign=top>Event</td><td>The event in which the deck was played.</td></tr>
  <tr><td valign=top>Rank</td><td>The ranking of the deck.</td></tr>
  <tr><td valign=top>Date</td><td>The date of the event.</td></tr>
  <tr><td valign=top>Creatures</td><td>The number of Creatures in the deck.</td></tr>
  <tr><td valign=top>Instants_Sorceries</td><td>The number of Instants and Sorceries in the deck.</td></tr>
  <tr><td valign=top>Other_spells</td><td>The number of Other Spells in the deck.</td></tr>
  <tr><td valign=top>Lands</td><td>The number of Lands in the deck.</td></tr>
</table>
