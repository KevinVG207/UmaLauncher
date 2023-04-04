import os
import UnityPy
import time

def main():
    t1 = time.perf_counter()
    hash = r"FQ4G5YZZYVH3PCCN7QGF6O7MXPKB3E2V"
    bundle_path = str(os.path.join(os.path.expandvars(r"%userprofile%\appdata\locallow\Cygames\umamusume\dat"), hash[:2], hash))
    env = UnityPy.load(bundle_path)
    for obj in env.objects:
        r_obj = obj.read()
        if r_obj.name.startswith("utx_ico_performance_"):
            r_obj.image.save(r_obj.name + ".png")
    t2 = time.perf_counter()
    print(f"Time: {(t2 - t1)}")


if __name__ == "__main__":
    main()
