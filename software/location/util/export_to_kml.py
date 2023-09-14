import simplekml
kml = simplekml.Kml()
ls = kml.newlinestring(name='A LineString')
ls.description = ''
ls.timestamp.when = ''
ls.coords = [(18.333868, -34.038274, 10.0), (18.370618, -34.034421, 10.0)]
ls.extrude = 1
ls.altitudemode = simplekml.AltitudeMode.relativetoground
ls.style.linestyle.width = 5
ls.style.linestyle.color = simplekml.Color.blue
kml.save('LineString Styling.kml')
