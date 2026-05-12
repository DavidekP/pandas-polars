# Analýza výkonu solárních panelů (Pandas vs Polars)

Tento repozitář obsahuje řešení analýzy fyzikálního datasetu pomocí dvou datových knihoven v Pythonu: `pandas` a `polars`. 

## 1. Postup čištění dat
Při úvodní analýze bylo zjištěno, že numerické sloupce (napětí, proud) se načetly jako text kvůli nečistotám v datech. Čištění proběhlo v těchto krocích:
1. **Přetypování (Casting):** Chybné řetězce u číslic byly nahrazeny `NaN` (v pandas) či `null` (v polars). 
2. **Logické filtry:** Odstraněny záporné hodnoty fyzikálních veličin (napětí, proud, výkon nemohou být při tomto měření záporné) a úhly mimo reálný rozsah 0-90°.
3. **Odstranění nulových hodnot a duplicit.**
4. **Sjednocení textu:** Metodami pro práci s řetězci byly vymazány přebytečné mezery a překlep "suny" byl nahrazen za "sunny".

## 2. Odpovědi na otázky ze zadání

**Úloha 1: Které sloupce vypadají problematicky?**
Sloupce `voltage_v` a `current_a` obsahovaly textové poznámky a systém je vyhodnotil jako `object` (string). Problémem byl i čas (`timestamp`), který měl nekonzistentní formát.

**Úloha 2: Jaké typy chyb jsi našel?**
Překlepy ve stringových sloupcích (suny), text v číselných polích, záporné hodnoty u vzdáleností nebo napětí a chybějící údaje (`NaN`). 

**Úloha 3: Jsou hodnoty power_w a power_calc stejné? Pokud ne, proč?**
Zcela se neshodují. Ačkoliv platí fyzikální vzorec $P = U \cdot I$, v praxi vznikají mírné rozdíly z důvodu zaokrouhlování na měřících přístrojích, šumu na senzorech, případně drobným časovým zpožděním v měření napětí a proudu senzorem (neodehrálo se to na nanosekundu přesně).

**Úloha 4: Jak úhel ovlivňuje výkon? Dává to fyzikální smysl?**
Ano. Výkon panelu je nejvyšší, když na něj paprsky dopadají kolmo (Lambertův kosinový zákon). S rostoucím odklonem úhlu plocha panelu vystavená svazku záření efektivně klesá a výkon jde dolů.

**Úloha 5: Jak silná je závislost intenzity světla a výkonu? Je lineární?**
Korelace mezi intenzitou (`lux`) a výkonem (`W`) se blížila 1.0 (velmi vysoká a kladná). Do určité míry je přímá (lineární) – více fotonů vybudí více elektronů. V extrémních hodnotách ale panel dosahuje svého konstrukčního maxima a roste jeho teplota, čímž začne linearita slábnout.

**Úloha 6: Kde panel funguje lépe a proč?**
Panel dosahuje výrazně lepších výsledků venku (Outdoor/Sunny) než pod lampou v učebně. Důvodem je nesrovnatelně větší světelný tok přímo ze slunce a fakt, že solární panely jsou optimalizovány pro široké sluneční barevné spektrum (lampy vysílají jen úzké frekvence světla).

**Úloha 7: Jak bys optimalizoval experiment?**
Nejlepší výsledky byly u přímého slunce při ideálním úhlu. Do budoucna bych doporučil měřit na střeše s "trackerem" (stojan, co se sám natáčí za sluncem) a zajistit chlazení panelů.

**Úloha 8: Jsou extrémní hodnoty chyby, nebo zajímavý jev?**
Většinou jde o chyby způsobené hardwarovou závadou senzoru multimetru. Může se však jednat i o tzv. "albedo" jev v laboratoři – zrcadlový odraz slunce od okolního skla do panelu, čímž dočasně vzrostla intenzita nad normální limit slunce. 

**Úloha 9: Vlastní analýza (Nejefektivnější panel)**
Porovnávali jsme průměrný výkon dle `panel_id` (`groupby`). Zjistili jsme, že některé panely dávají při stejných podmínkách horší výkon než jiné, což poukazuje na jejich výrobní vady, opotřebení, nebo nečistoty na povrchu.

## 3. Porovnání Pandas vs Polars

**Pandas:**
* **Klady:** Má ho obrovská komunita, na internetu se snadno hledají rady a řešení (StackOverflow). Jeho syntaxe je velmi intuitivní pro začátečníky.
* **Zápory:** Při extrémně velkých datasetech (miliony řádků) začíná být paměťově velmi náročný a pomalý.

**Polars:**
* **Klady:** Je neuvěřitelně rychlý (napsaný v jazyce Rust), využívá všechna jádra procesoru (multithreading) a má velmi pěknou čistou sémantiku (`df.with_columns`, `df.filter`), která se navíc dá krásně zřetězovat za sebe (tzv. *method chaining*).
* **Zápory:** Knihovna je mladší, existuje méně návodů na internetu, syntaxe pomocí "expressions" (např. `pl.col('nazev_sloupce')`) je pro někoho zvyklého na obyčejné závorky z Pandas trochu nepřehledná na učení.
