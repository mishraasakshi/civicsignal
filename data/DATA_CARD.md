# Dataset Card — CivicSignal (Amity University Lucknow Pilot)

---

## 1. Dataset Summary
This dataset contains facility and campus complaints specifically designed for university environments with heavy multilingual (English and Romanized Hinglish) and informal writing characteristics.

- **Primary Setting**: Amity University Lucknow Hostels & Campus Facilities.
- **Languages**: English, Romanized Hinglish (*"paani nahi aa raha"*, *"wifi down hai"*), mixed slang, abbreviations, and informal colloquialisms.
- **Categories (8 Fixed Domains)**:
  1. `water_plumbing` (leaks, low water pressure, broken taps, geyser issues, clogged drains)
  2. `electrical` (lights flickering, power outages, sparking sockets, broken fans, AC issues)
  3. `cleanliness` (uncleaned washrooms, overflowing dustbins, litter, corridor garbage)
  4. `internet_wifi` (hostel Wi-Fi down, slow portal connection, DNS errors, router unpowered)
  5. `furniture` (broken study table, creaking bed, loose chair wheel, broken cupboard latch)
  6. `mess_food` (undercooked food, unhygienic dining hall, cold breakfast, food shortage)
  7. `security` (broken main gate latch, unauthorized trespass, missing bike, guard post empty)
  8. `other` (noise disturbance, pest complaints, parking space disputes)

---

## 2. Dataset Sources & Splits
| Split | Source | Size Target | Role |
| :--- | :--- | :---: | :--- |
| **Train** | Synthetic (Groq API generated) | ~3,500 | Training classical & embedding classifiers |
| **Validation** | Synthetic (Groq API generated) | ~500 | Hyperparameter tuning and model checkpointing |
| **Test** | Real Student Complaints (Google Form) | 150–300 | **Real-only test set** (never trained on) |
| **Pairs** | Hand-labelled duplicate evaluation set | 300–500 pairs | Evaluating duplicate retrieval (Model B) |

---

## 3. Campus Locations (Amity University Lucknow Coordinates)
Approximate coordinate centroids for landmark tagging:
1. `Hostel A - Boys (Malhar)`: 26.8580, 80.9990
2. `Hostel B - Boys`: 26.8584, 80.9995
3. `Hostel C - Girls`: 26.8572, 80.9982
4. `Hostel D - Girls`: 26.8576, 80.9986
5. `Main Campus Gate`: 26.8565, 80.9975
6. `Central Library`: 26.8590, 81.0002
7. `Main Canteen & Food Court`: 26.8582, 81.0008
8. `Academic Block 1 (Engineering)`: 26.8595, 81.0010
9. `Academic Block 2 (Management)`: 26.8598, 81.0015
10. `Academic Block 3 (Law & Humanities)`: 26.8602, 81.0020
11. `Academic Block 4`: 26.8605, 81.0025
12. `Sports Ground & Pavilion`: 26.8568, 81.0018
13. `Student Parking Lot`: 26.8562, 80.9980
14. `Auditorium Complex`: 26.8588, 81.0012
15. `Health Center & Clinic`: 26.8578, 80.9978

*(Coordinates are approximate campus centroids for local spatial clustering demonstration)*

---

## 4. Known Gaps and Limitations
1. **Synthetic-to-Real Domain Gap**: Models trained solely on LLM-generated text may exhibit slight divergence when confronted with novel campus slang or localized Hindi dialects. The held-out real student test set is strictly designed to measure this gap.
2. **Coordinate Precision**: Students submit landmark pins or text mentions rather than high-precision GPS geodetic survey coordinates.
