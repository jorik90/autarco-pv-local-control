# Autarco Omvormer Lokaal Uitlezen (Zonder Invrida-abonnement)

> 🇬🇧 **English version available:** [Read this documentation in English (`README.en.md`)](README.en.md)

Nadat zonnepanelen- en omvormerleverancier **Autarco** failliet is verklaard, zijn de software en het monitoringplatform (`my.autarco.com`) overgenomen door **Invrida** (`my.invrida.com`). Waar het uitlezen van je eigen zonnepanelen voorheen inbegrepen was bij de aanschaf van het systeem, vraagt Invrida inmiddels **€ 30,- per jaar (€ 2,50 per maand)** om toegang te houden tot de app en je eigen opbrengstgegevens. Betaal je niet, dan wordt je toegang tot de app en `my.invrida.com` afgesloten.

Gelukkig ben je voor het uitlezen, monitoren en aansturen van je Autarco-omvormer **helemaal niet afhankelijk van de cloud van Autarco of Invrida**. Onder de motorkap zijn Autarco-omvormers namelijk gebouwd door **Solis (Ginlong)** en voorzien van een netwerkstick die op je eigen thuisnetwerk standaard **Modbus TCP (poort 502)** spreekt.

In deze repository vind je:
1. Een kant-en-klaar **Python CLI-script** ([`autarco_reader.py`](autarco_reader.py)) zonder externe dependencies om je omvormer direct uit te lezen naar je terminal, JSON of CSV.
2. Volledige **Home Assistant-instructies** (zowel via de HACS *Solis Modbus* integratie als via de ingebouwde Home Assistant Modbus YAML in [`homeassistant_modbus.yaml`](homeassistant_modbus.yaml)).
3. Het complete **Modbus-registeroverzicht** (uitlezen én aansturen/curtailment bij negatieve stroomprijzen).
4. Instructies om het **doorsturen van jouw data naar de Invrida-cloud uit te zetten**.

---

## Achtergrond: Van Autarco naar betaald Invrida-abonnement

Eigenaren van een Autarco-systeem ontvingen onderstaande aankondiging van Invrida:

> **Wat er verandert**  
> Voor jouw systeem loopt op dit moment geen abonnement op de monitoring. Wil je je app, je overzicht en je opbrengstgeschiedenis houden, dan sluit je die zelf af. Gebeurt dat niet, dan sluit daarna je toegang tot de app en tot `my.invrida.com`.
>
> **€ 30 per jaar**  
> Dat is € 2,50 per maand voor het volledig blijven volgen van je systeem. [...]  
> *Waarom hier een bedrag aan hangt: de software, de servers en de opslag van jouw gegevens werden tot nu toe betaald uit de verkoop van zonnepanelen en omvormers. Je betaalde er dus altijd al voor — alleen niet zichtbaar, want het zat verwerkt in de prijs van je installatie. Invrida verkoopt geen panelen; wij maken alleen de software. Daarom is de monitoring nu een dienst met een eigen prijs.*

Met de tools en instellingen in deze repository houd je zelf 100% gratis, lokaal en realtime inzicht in al je zonnepaneeldata (én veel gedetailleerder dan in de standaard app).

---

## Geteste Hardware

* **Autarco Omvormer:** `Autarco S2.LD6000-MIII` (3-fase string-omvormer, 6 kW, 2 MPPT's)
  * Onderliggend OEM-platform: **Solis / Ginlong 3P(3-20)K-4G** (`Product Model 0x0503`, DSP `0x003B`, LCD `0x0084`)
* **Datalogger (LAN/WiFi-stick):** Solis/Ginlong embedded lwIP `1.3.1` module (`Web Ver: 2.4.0`, firmware `10010119`)
* **Protocol:** Standaard **Modbus TCP** op poort **`502`**, Slave/Unit ID **`1`**

*(Heb je een andere Autarco string-omvormer uit de S1- of S2-serie met een LAN- of WiFi-stick waarop poort 502 openstaat? Dan werkt deze opzet vrijwel identiek).*

---

## 1. Uitlezen met het Python Script (`autarco_reader.py`)

Het script [`autarco_reader.py`](autarco_reader.py) gebruikt uitsluitend de standaardbibliotheek van Python 3 (geen `pip install` nodig).

### Gebruik

```bash
# 1. Overzichtelijke tabel in de terminal (vervang 192.168.1.100 door het IP-adres van jouw omvormer)
./autarco_reader.py --host 192.168.1.100

# Je kunt het IP-adres ook via een omgevingsvariabele meegeven:
export AUTARCO_HOST=192.168.1.100
./autarco_reader.py

# 2. Uitvoer als JSON (handig voor eigen scripts, MQTT of Telegraf/Node-RED)
./autarco_reader.py --host 192.168.1.100 --format json

# 3. Meting toevoegen aan een CSV-logbestand
./autarco_reader.py --host 192.168.1.100 --csv-file metingen.csv

# 4. Continu monitoren (bijv. elke 15 seconden)
./autarco_reader.py --host 192.168.1.100 --watch 15
```

### Voorbeelduitvoer

```text
============================================================
 Autarco / Solis Omvormer (192.168.1.100) - 2026-06-15T13:30:00
============================================================
 Serienummer       : 1805XXXXXXXXXXXX
 Status            : Normaal in bedrijf (Generating) (code 3)
 Tijd op omvormer  : 2026-06-15 13:30:00
------------------------------------------------------------
 ACTUEEL VERMOGEN & TEMPERATUUR
   AC Vermogen     : 2500 W
   DC Vermogen     : 2600 W
   Temperatuur     : 32.5 °C
   Netfrequentie   : 50.00 Hz
------------------------------------------------------------
 ENERGIE OPBRENGST
   Vandaag         : 12.5 kWh
   Gisteren        : 18.0 kWh
   Deze maand      : 210 kWh
   Vorige maand    : 450 kWh
   Dit jaar        : 3200 kWh
   Vorig jaar      : 5100 kWh
   Totaal (Leven)  : 10500 kWh
------------------------------------------------------------
 ZONNEPANELEN (DC STRINGS)
   String 1 (PV1)  : 380.0 V  |  3.4 A  | 1292.0 W
   String 2 (PV2)  : 385.0 V  |  3.4 A  | 1309.0 W
   DC Busspanning  : 610.0 V
------------------------------------------------------------
 NETZIJDE (AC 3-FASE)
   Fase L1         : 230.1 V  |  3.6 A
   Fase L2         : 230.5 V  |  3.6 A
   Fase L3         : 231.0 V  |  3.6 A
============================================================
```

---

## 2. Koppelen aan Home Assistant

Je kunt kiezen uit twee methodes in Home Assistant:
* **Optie A (via UI / HACS):** Met de bestaande `Solis Modbus` integratie (inclusief sturing & automatische kloksynchronisatie).
* **Optie B (zonder HACS, ingebouwd in Home Assistant):** Via de standaard `modbus:` integratie in `configuration.yaml`.

> **Belangrijk:** De netwerkstick van de omvormer staat **slechts één gelijktijdige TCP-verbinding op poort 502** toe. Zorg dus dat je niet tegelijk Optie A én Optie B (of een continu Python-script) laat verbinden.

### Optie A: Via HACS (`Pho3niX90/solis_modbus`)

1. Installeer in **HACS** de integratie **Solis Modbus** (`https://github.com/Pho3niX90/solis_modbus`) en herstart Home Assistant.
2. Ga naar **Instellingen** → **Apparaten & Diensten** → **Integratie toevoegen** → zoek op **Solis Modbus**.
3. **Scherm 1 (Connection Method):** Kies **`S2_WL_ST`**.
4. **Scherm 2 (Inverter Configuration):** Vul voor de **Autarco S2.LD6000-MIII** het volgende in:
   * **IP Address:** Het lokale IP-adres van je omvormer (bijv. `192.168.1.100`)
   * **Port:** `502`
   * **Modbus Slave ID:** `1`
   * **Inverter Model:** **`3P(3-20)K-4G`** *(of `S5-GR3P`)*
   * **Inverter Serial:** Je 16-cijferige omvormer-serienummer *(te vinden via `./autarco_reader.py` of op de sticker van de omvormer)*
   * **Poll profile:** `Normal` *(gebruik **niet** `Extreme`)*
   * **Fast / Normal / Slow Poll Interval:** `15` / `30` / `60` seconden
5. **Vinkjes (Checkboxes) op Scherm 2:**
   * ✅ **Has PV (Solar Panels):** **AAN**
   * ✅ **Suppress 'datalogger unreachable' repair issue while the sun is below the horizon:** **AAN** *(voorkomt foutmeldingen 's nachts als de omvormer slaapt)*
   * ✅ **Automatically correct inverter clock drift (`clock_sync`):** **AAN** *(houdt de klok van de omvormer automatisch op tijd zonder cloud)*
   * ❌ **Zet alle overige vinkjes UIT** (`Updated to V2 Firmware`, `Has Battery Storage`, `Has HV Battery`, `Has Generator`, `Has AC Coupling`, `Parallel inverter`, `Second smart meter`, `EPM / export power manager`, `Extreme` opties).

### Optie B: Via ingebouwde Home Assistant Modbus (`configuration.yaml`)

Gebruik je geen HACS? Neem dan de inhoud van [`homeassistant_modbus.yaml`](homeassistant_modbus.yaml) over in je `configuration.yaml` (pas `host:` aan naar jouw IP-adres) en herstart Home Assistant. Koppel daarna `sensor.autarco_opbrengst_totaal` aan het **Home Assistant Energie-dashboard**.

---

## 3. Eigen Webinterface van de Datalogger (`http://<IP>/`)

De LAN-stick in de omvormer draait ook een ingebouwde webpagina op poort 80:
* **URL:** `http://<IP-ADRES>/` (bijv. `http://192.168.1.100/`)
* **Standaard gebruikersnaam:** `admin`
* **Standaard wachtwoord:** `123456789`

**Let op:** Door een bug in de Solis/Autarco stick-firmware (`Web Ver 2.4.0` / `10010119`) toont `status.html` (`inverter.cgi`) op deze ingebouwde pagina alleen het serienummer en blijft het vermogen en de opbrengst op `0 W` / `0 kWh` staan. Pas de firmware van de stick **niet** aan om dit te verhelpen: het risico is groot dat een nieuwere firmware poort `502` (Modbus TCP) dichtzet, waardoor je helemaal geen lokale toegang meer hebt.

---

## 4. Upload naar de Invrida / Autarco Cloud blokkeren

Zelfs zonder betaald abonnement blijft de stick op de achtergrond je opbrengstdata doorsturen naar de externe cloud-server (`Remote server A: Connected`). Je kunt dit eenvoudig blokkeren terwijl lokale toegang via Modbus TCP op je thuisnetwerk gewoon blijft werken.

### Methode 1: In je router (bijv. Ubiquiti EdgeRouter X)
1. **Geef de omvormer een vast IP-adres (DHCP Static Mapping):**
   * Ga in de EdgeRouter naar **Services** → **DHCP Server** → **View Leases** en maak een *Static MAC/IP Mapping* aan voor het MAC-adres van de stick.
2. **Blokkeer uitgaand internetverkeer in de Firewall:**
   * Ga naar **Firewall/NAT** → **Firewall Policies** → kies je `WAN_OUT` (of `LAN_IN`) ruleset.
   * Voeg een regel toe met **Action: Drop**, **Protocol: All protocols**, en bij **Source** het IP-adres (of MAC-adres) van de omvormer.

### Methode 2: Op een Fritz!Box
1. Ga naar **Internet** → **Filters** → **Kinderslot (Parental Controls)**.
2. Zoek het IP-adres van de omvormer op en kies **Internetgebruik blokkeren**.

### Methode 3: Direct op de stick zelf (via Statisch IP zonder Gateway)
1. Log in op `http://<IP-ADRES>/` (`admin` / `123456789`) → **Advanced** → **LAN settings**.
2. Zet de modus op **Static IP**:
   * **IP Address:** Je huidige lokale IP-adres (bijv. `192.168.1.100`)
   * **Subnet Mask:** `255.255.255.0`
   * **Default Gateway:** `192.168.1.254` *(een ongebruikt IP-adres in je subnet dat géén router is)*
   * **Preferred DNS:** `127.0.0.1`
3. Klik op **Save** en herstart de stick via **Restart**. De stick kan nu alleen nog binnen je eigen LAN communiceren en kan het internet niet meer op.

---

## 5. Compleet Modbus Registeroverzicht (`S2.LD6000-MIII`)

### A. Uitlezen — Input Registers (Function Code `0x04`)
*(Alle onderstaande adressen zijn 0-based protocol-adressen zoals direct op de draad en in Home Assistant gebruikt).*

| Adres (0-based) | Parameter | Type | Schaal / Eenheid | Opmerking |
| :--- | :--- | :--- | :--- | :--- |
| `2999` | Product Model | `U16` | Hex | `0x0503` op S2.LD6000-MIII |
| `3000` | DSP Software Version | `U16` | Hex | `0x003B` |
| `3001` | LCD Software Version | `U16` | Hex | `0x0084` |
| `3002` | AC Output Type | `U16` | Enum | `1` = 3-fase 4-draads |
| `3003` | DC Input Type | `U16` | Enum | `1` = 2 MPPT / DC-ingangen |
| `3004–3005` | **AC Actief Vermogen** | `U32` | `1 W` | Actueel teruggeleverd vermogen |
| `3006–3007` | **DC Totaal Vermogen** | `U32` | `1 W` | Actueel vermogen van zonnepanelen |
| `3008–3009` | **Opbrengst Totaal (Levensduur)** | `U32` | `1 kWh` | Cumulatief totaal sinds installatie |
| `3010–3011` | **Opbrengst Deze Maand** | `U32` | `1 kWh` | Huidige kalendermaand |
| `3012–3013` | **Opbrengst Vorige Maand** | `U32` | `1 kWh` | Vorige kalendermaand |
| `3014` | **Opbrengst Vandaag** | `U16` | `0.1 kWh` | Dagopbrengst vandaag |
| `3015` | **Opbrengst Gisteren** | `U16` | `0.1 kWh` | Dagopbrengst gisteren |
| `3016–3017` | **Opbrengst Dit Jaar** | `U32` | `1 kWh` | Huidig kalenderjaar |
| `3018–3019` | **Opbrengst Vorig Jaar** | `U32` | `1 kWh` | Vorig kalenderjaar |
| `3021` | **DC Spanning String 1 (PV1)** | `U16` | `0.1 V` | MPPT 1 spanning |
| `3022` | **DC Stroom String 1 (PV1)** | `U16` | `0.1 A` | MPPT 1 stroom |
| `3023` | **DC Spanning String 2 (PV2)** | `U16` | `0.1 V` | MPPT 2 spanning |
| `3024` | **DC Stroom String 2 (PV2)** | `U16` | `0.1 A` | MPPT 2 stroom |
| `3029` | Fout-/Alarmcode (Fault Code) | `U16` | Bitmask | `0` = Geen storing |
| `3030` | DC Busbar Half-spanning (+) | `U16` | `0.1 V` | Positieve DC-bus helft |
| `3031` | **DC Busbar Spanning (Totaal)** | `U16` | `0.1 V` | Totale interne DC-busspanning |
| `3032` | DC Busbar Half-spanning (-) | `U16` | `0.1 V` | Negatieve DC-bus helft |
| `3033` | **AC Spanning Fase L1** | `U16` | `0.1 V` | Netspanning fase 1 |
| `3034` | **AC Spanning Fase L2** | `U16` | `0.1 V` | Netspanning fase 2 |
| `3035` | **AC Spanning Fase L3** | `U16` | `0.1 V` | Netspanning fase 3 |
| `3036` | **AC Stroom Fase L1** | `U16` | `0.1 A` | Netstroom fase 1 |
| `3037` | **AC Stroom Fase L2** | `U16` | `0.1 A` | Netstroom fase 2 |
| `3038` | **AC Stroom Fase L3** | `U16` | `0.1 A` | Netstroom fase 3 |
| `3040` | Werkmodus (Working Mode) | `U16` | Code | `0`=Geen, `1`=Volt-Watt, `2`=Volt-VAr, `3`=Fixed PF |
| `3041` | **Omvormer Temperatuur** | `S16` | `0.1 °C` | Interne IGBT-temperatuur |
| `3042` | **Netfrequentie** | `U16` | `0.01 Hz` | bijv. `5000` = `50.00 Hz` |
| `3043` | **Bedrijfsstatus (Status)** | `U16` | Code | `0`=Waiting, `1`=Open Run, `2`=Soft Run, `3`=Generating |
| `3049` | Actuele Vermogenslimiet | `U16` | `0.01 %` | `11000` = `110.00%` |
| `3053` | Netprofiel / Grid Standard | `U16` | Code | `14` = EN50549 (NL) |
| `3055–3056` | Blindvermogen (Reactive Power) | `S32` | `1 VAr` | Actueel blindvermogen |
| `3057–3058` | Schijnbaar vermogen (Apparent) | `S32` | `1 VA` | Actueel schijnbaar vermogen |
| `3059` | Power Factor (`cos φ`) | `S16` | `0.001` | `1000` = `1.000` |
| `3060–3063` | Serienummer (4 woorden) | `U16[4]` | Hex (omgekeerd per woord) | Elke `U16` in hex achterstevoren lezen |
| `3072–3077` | Interne Klok (J, M, D, U, M, S) | `U16[6]` | Jaar + 2000 | Tijdstip op de omvormer |

### B. Configureren / Aansturen — Holding Registers (Function Code `0x06` / `0x10`)

Handig voor dynamische energiecontracten (omvormer terugregelen of uitschakelen bij negatieve stroomprijzen):

* **Omvormer AAN / UIT schakelen (Remote On/Off):**
  * Register `3007` (of `3006` 0-based):
    * Schrijf `0xBE` (`190`) = **Omvormer AAN (Start)**
    * Schrijf `0xDE` (`222`) = **Omvormer UIT (Stand-by / Stop)**
* **Vermogensbegrenzing / Curtailment (0% – 110%):**
  1. Zet eerst de *Power Limitation Switch* aan op register `3070` (of `3069` 0-based):
     * `0xAA` (`170`) = **Begrenzing AAN**
     * `0x55` (`85`) = **Begrenzing UIT**
  2. Schrijf het gewenste percentage naar register `3052` (of `3051` 0-based) met schaal `0.01%` (bijv. `5000` = `50%`, `0` = `0%`, `10000` = `100%`).
* **Systeemtijd / Klok instellen:**
  * Registers `3000 t/m 3005` (of `2999 t/m 3004` 0-based): Jaar (`0–99`), Maand (`1–12`), Dag (`1–31`), Uur (`0–23`), Minuut (`0–59`), Seconde (`0–59`).

---

## Hoe dit is uitgezocht (Zelf reproduceren met AI)

Dit volledige onderzoek, het reverse-engineeren van de omvormer op het lokale netwerk, het achterhalen van de Modbus-registermap en het schrijven van de code en documentatie is uitgevoerd door AI met **Google Antigravity** (draaiend op **Windows met Ubuntu WSL**) en het model **Gemini 4 Argon (Medium)**.

> **Waarom vanuit Ubuntu WSL / Linux?**  
> Linux (en daarmee Ubuntu onder WSL op Windows) heeft standaard veel meer krachtige netwerk-, tekst- en ontwikkeltooling aan boord dan een standaard Windows-omgeving (`cmd` / PowerShell). Tools zoals `python3` (voor directe ruwe TCP/UDP-sockets en binaire Modbus-structuren), `curl` (zonder PowerShell-aliassen, met directe ondersteuning voor rauwe HTTP-headers), `ping`, `ip`, `grep`, `tr` (bijv. om null-bytes uit kapotte embedded CGI-responses te filteren) en `git` zijn direct beschikbaar. Daardoor kan een AI-agent vanuit WSL zonder tussenstappen of extra installaties snel netwerkprotocollen analyseren, binaire pakketten sturen en antwoorden parsen.

Heb je zelf een ander type omvormer of slim apparaat waarvan de fabrikant failliet is of geld gaat vragen voor de cloud? Zo kun je dit zelf in een paar minuten met Antigravity (of een vergelijkbare agentic coding tool) reproduceren:

1. **Zorg dat je WSL / Linux-terminal op hetzelfde netwerk zit als de omvormer** en zoek het IP-adres van de omvormer op in je router.
2. **Geef de AI-agent een prompt zoals:**
   > *"De fabrikant van mijn omvormer (<Merk / Type>) is failliet en ik kan niet meer bij mijn data. Zorg dat ik de omvormer lokaal kan uitlezen. Het IP-adres is `<IP-ADRES>`."*
3. **Wat de AI-agent vervolgens zelfstandig uitvoert vanuit WSL:**
   * **Poortscan:** Scant veelvoorkomende omvormer-poorten op het lokale IP-adres (zoals TCP `80`, `443`, `502` voor Modbus TCP, `8899` voor Solarman V5, en UDP `48899`).
   * **HTTP- & OEM-identificatie:** Inspecteert de HTTP-headers en ingebouwde webpagina's op poort `80` (waarmee bij Autarco direct bleek dat de webserver `WWW-authenticate: Basic realm="solis"` op een `lwIP/1.3.1` stack draait met standaardwachtwoord `admin` / `123456789`).
   * **Modbus-registerscan:** Stuurt test-requests naar poort `502` (Function Code `0x04` Input Registers en `0x03` Holding Registers), leest de ruwe waarden uit (zoals `2999–3079`) en legt die naast de Solis/Ginlong Modbus-specificaties om de exacte schaling, endianness en het serienummer te verifiëren.
   * **Integratie & Code genereren:** Schrijft direct een kant-en-klaar uitleesscript en zoekt in de broncode van bestaande Home Assistant-integraties (zoals `Pho3niX90/solis_modbus`) op welke model-templates (`3P(3-20)K-4G`) exact overeenkomen met de gevonden registers.

---

## Licentie

Dit project valt onder de [MIT License](LICENSE) — vrij te gebruiken, aan te passen en te delen.

