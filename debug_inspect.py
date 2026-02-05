import nbafg

players, _ = nbafg.main()

for name in ("RayJ Dennis", "Christian Koloko"):
    matches = [p for p in players if p['Player'] == name]
    print(name, 'count=', len(matches))
    for m in matches:
        print(' ', m)
