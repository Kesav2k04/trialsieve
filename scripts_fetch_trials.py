import json, urllib.request, urllib.parse, time, os, re
CONDS = ["type 2 diabetes","chronic kidney disease","heart failure","COPD","hypertension","coronary artery disease"]
FIELDS = "NCTId,BriefTitle,OfficialTitle,EligibilityCriteria,MinimumAge,MaximumAge,Sex,HealthyVolunteers,Condition,OverallStatus,Phase,StudyType,LeadSponsorName,StudyFirstPostDate"
out=[]
for c in CONDS:
    q = urllib.parse.urlencode({
        "query.cond": c, "filter.overallStatus":"RECRUITING",
        "fields": FIELDS, "pageSize":"40",
        "aggFilters":"studyType:int",
    })
    url=f"https://clinicaltrials.gov/api/v2/studies?{q}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            d=json.load(r)
    except Exception as e:
        print("ERR",c,e); continue
    for s in d.get("studies",[]):
        p=s.get("protocolSection",{})
        elig=p.get("eligibilityModule",{})
        txt=elig.get("eligibilityCriteria","") or ""
        out.append({
            "nct": p.get("identificationModule",{}).get("nctId"),
            "title": p.get("identificationModule",{}).get("briefTitle"),
            "cond_query": c,
            "conditions": p.get("conditionsModule",{}).get("conditions",[]),
            "minAge": elig.get("minimumAge"), "maxAge": elig.get("maximumAge"),
            "sex": elig.get("sex"), "healthy": elig.get("healthyVolunteers"),
            "phase": p.get("designModule",{}).get("phases"),
            "sponsor": p.get("sponsorCollaboratorsModule",{}).get("leadSponsor",{}).get("name"),
            "criteria": txt,
        })
    time.sleep(0.4)
# score by how "record-checkable" the criteria look
NUM = re.compile(r"\b\d+(\.\d+)?\s*(%|mg/dL|mmol/L|mL/min|kg/m2|kg/m\^2|years?|months?|weeks?|days?)", re.I)
KEY = ["hba1c","egfr","creatinine","bmi","ldl","hdl","triglyceride","systolic","diastolic","ejection fraction",
       "metformin","insulin","statin","ace inhibitor","arb","diuretic","within the past","within the last",
       "history of","diagnosis of","aged","age ","years of age","prior to screening"]
for t in out:
    c=t["criteria"].lower()
    t["n_bullets"]=len([l for l in t["criteria"].split("\n") if l.strip().startswith("*")])
    t["n_num"]=len(NUM.findall(t["criteria"]))
    t["n_key"]=sum(c.count(k) for k in KEY)
    t["score"]=t["n_num"]*3 + t["n_key"] + min(t["n_bullets"],30)
    t["len"]=len(t["criteria"])
out=[t for t in out if 400 < t["len"] < 9000 and t["n_bullets"]>=8]
out.sort(key=lambda x:-x["score"])
json.dump(out, open("data/work/trials/candidates.json","w"), indent=1)
print(f"{len(out)} candidates")
for t in out[:14]:
    print(f'{t["score"]:4d} b={t["n_bullets"]:3d} num={t["n_num"]:3d} {t["nct"]}  {t["cond_query"][:22]:24s} {t["title"][:64]}')
