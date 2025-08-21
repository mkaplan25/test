from pycalphad import Database

# TDB dosyasını yükle
db = Database(r"C:\\Users\\user\\PycharmProjects\\AlloyCraft\\Termodinamik\\FeC.tdb")
# Elementleri yazdır
print("ELEMENTS:")
for elem in db.elements:
    print("-", elem)

# Fazları yazdır
print("\nPHASES:")
for phase_name in db.phases:
    phase = db.phases[phase_name]
    print(f"-{phase_name}")
    #print(f"- {phase_name}: Sublattice = {phase.sublattices}")

# Parametre sayısı
print(f"\nToplam faz sayısı: {len(db.phases)}")
print(f"\nToplam termodinamik parametre sayısı: {len(db._parameters)}")


