import json, os, sys, collections, datetime
SRC="data/work/synthea/fhir"
OUT="data/work/patient_index.json"
files=sorted(f for f in os.listdir(SRC) if not f.startswith(("hospital","practitioner")))
idx=[]
cond_ct=collections.Counter(); obs_ct=collections.Counter(); med_ct=collections.Counter()
for i,f in enumerate(files):
    try:
        b=json.load(open(os.path.join(SRC,f),encoding="utf-8"))
    except Exception as e:
        print("skip",f,e); continue
    rec={"file":f,"conds":set(),"meds":set(),"obs":{},"id":None,"birth":None,"sex":None,"deceased":False,"n_res":0}
    for e in b.get("entry",[]):
        r=e.get("resource",{}); rt=r.get("resourceType"); rec["n_res"]+=1
        if rt=="Patient":
            rec["id"]=r.get("id"); rec["birth"]=r.get("birthDate"); rec["sex"]=r.get("gender")
            rec["deceased"]= bool(r.get("deceasedDateTime"))
            rec["deceasedDate"]=r.get("deceasedDateTime")
        elif rt=="Condition":
            for c in r.get("code",{}).get("coding",[]):
                rec["conds"].add(c.get("display","")); cond_ct[c.get("display","")]+=1
        elif rt=="MedicationRequest":
            for c in r.get("medicationCodeableConcept",{}).get("coding",[]):
                rec["meds"].add(c.get("display","")); med_ct[c.get("display","")]+=1
        elif rt=="Observation":
            for c in r.get("code",{}).get("coding",[]):
                d=c.get("display","")
                obs_ct[d]+=1
                v=r.get("valueQuantity")
                if v is not None:
                    dt=r.get("effectiveDateTime","")
                    prev=rec["obs"].get(d)
                    if prev is None or dt>prev[1]:
                        rec["obs"][d]=(v.get("value"), dt, v.get("unit"))
    rec["conds"]=sorted(x for x in rec["conds"] if x)
    rec["meds"]=sorted(x for x in rec["meds"] if x)
    idx.append(rec)
    if (i+1)%100==0: print("...",i+1,flush=True)
json.dump({"patients":idx},open(OUT,"w"),indent=0)
print("indexed",len(idx))
print("\n=== TOP CONDITIONS ==="); [print(f"{n:5d}  {c}") for c,n in cond_ct.most_common(45)]
print("\n=== TOP OBSERVATIONS ==="); [print(f"{n:6d}  {c}") for c,n in obs_ct.most_common(40)]
print("\n=== TOP MEDS ==="); [print(f"{n:5d}  {c}") for c,n in med_ct.most_common(30)]
