# %%
import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.pyplot import figure
import plotly.express as px
from datetime import datetime


# %%
# merging the files for Network Audit
joined_files = os.path.join( "~\*Network-Audit.csv") #wilcard search - change to whatever you named your monthly files

# A list of all joined files is returned
joined_list = glob.glob(joined_files)

# Finally, the files are joined
pd_audit = pd.concat(map(pd.read_csv, joined_list), ignore_index=True)

#Create combined CSV

pd_audit.to_csv(r"~\1_25-5_26-Combined_Network-Audit.csv", index=False)

# %%
# merging the files for Network Audit
joined_files = os.path.join(r"~\*PD-Audit*.csv") #another wildcard search for local department files

# A list of all joined files is returned
joined_list = glob.glob(joined_files)

# Finally, the files are joined
df = pd.concat(map(pd.read_csv, joined_list), ignore_index=True)

#Create combined CSV

df.to_csv(r"~\1_25-5_26-Combined_PD-Audit.csv", index=False)


columns = ["Org_Name", "Time Frame", "Reason", "Case #", "Search Time", "Search Date"
           "Search Type", "Text Prompt", "Moderation", "Networks", "Count"]

df = pd.read_csv(r"~\Results.csv", header=None, names=columns)


print(df.head())
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
print(df.columns.tolist())




def hex_to_12hr(hex_str):
    ms = int(hex_str, 16)
    hours, remainder = divmod(ms, 3600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    period = "AM" if hours < 12 else "PM"
    hour_12 = hours % 12
    hour_12 = 12 if hour_12 == 0 else hour_12
    return f"{hour_12:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d} {period}"

df["Search Time"] = df["Search Time"].apply(hex_to_12hr)


# Step 1: Parse the column to datetime (strip " UTC" suffix first)
df['Search Time'] = df['Search Time'].str.replace(" UTC", "", regex=False)

# Step 2: Parse with format='mixed' so pandas infers per-row, and utc=True so
# everything becomes UTC-aware in one step (handles the naive "UTC"-suffixed
# rows AND the already-offset-aware ISO rows correctly, without a separate
# tz_localize step that would fail on already-aware timestamps)

df['Search Time'] = pd.to_datetime(df['Search Time'], format='mixed', utc=True)

# Step 3: Convert to Eastern
df['Search Time'] = df['Search Time'].dt.tz_convert("America/New_York")


# Step 3: Split into separate date and time columns
df['Search Date'] = df['Search Time'].dt.strftime("%m/%d/%Y")
df['Search_Time'] = df['Search Time'].dt.strftime("%I:%M:%S %p")

print(df[['Search Date', 'Search_Time']].head())


df['Search Hour'] = df['Search Time'].dt.hour

grouped = df.groupby(['Org_Name', 'Time Frame', 'Reason', 'Case #', 'Search Hour', 'Search Date',
                      'Text Prompt', 'Moderation'], 
                      dropna=False)[['Networks', 'Count']].sum().reset_index()

print(grouped['Count'].sum())  # should now match df['Count'].sum()

# %%
print(grouped.info())

split_cols = grouped['Time Frame'].str.split('\n', expand=True)

grouped['Start Time'] = split_cols[0]
grouped['End Time'] = split_cols[1]

# Step 1: Parse the column to datetime (strip " UTC" suffix first)
grouped['Start Time'] = grouped['Start Time'].str.replace(" UTC", "", regex=False)
grouped['End Time'] = grouped['End Time'].str.replace(" UTC", "", regex=False)
grouped['Start Time'] = pd.to_datetime(grouped['Start Time'], format="%m/%d/%Y, %I:%M:%S %p")
grouped['End Time'] = pd.to_datetime(grouped['End Time'], format="%m/%d/%Y, %I:%M:%S %p")

# Step 2: Localize as UTC, then convert to Eastern
grouped['Start Time'] = grouped['Start Time'].dt.tz_localize("UTC").dt.tz_convert("America/New_York")
grouped['End Time'] = grouped['End Time'].dt.tz_localize("UTC").dt.tz_convert("America/New_York")

grouped['Search Time Frame (Days)'] = grouped['End Time'] - grouped['Start Time']

print(grouped[['Start Time', 'End Time', 'Search Time Frame (Days)']].head())



# %%
grouped = grouped.groupby(['Org_Name', 'Search Time Frame (Days)', 'Reason', 'Case #', 'Search Hour', 'Search Date',
                           'Text Prompt', 'Moderation'], 
                      dropna=False)[['Networks', 'Count']].sum().reset_index()


print(grouped['Count'].sum())  # should now match df['Count'].sum()

# %%
import pandas as pd
import re




#orgs = pd.read_csv(r"C:\Users\hsand\.vscode\.venv\deflockdekalb\Flock_Network_Sharing_Lists_6-15-2026.csv")

orgs = df[['Org Name']].drop_duplicates().copy()


OUTPUT_PATH = r"~\Flock_Network_Sharing_Lists_6-15-2026_cleaned.csv"

# US state abbreviations for validation
STATE_ABBRS = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA',
    'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT',
    'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
}

# Org type phrases -> full names. Keys can be single- or multi-word;
# matching is done as word-boundary regex (case-insensitive), checked
# longest-key-first, against the punctuation-stripped "Org Name Cleaned"
# column -- so keys must NOT contain apostrophes, but output VALUES can.
ORG_TYPES = {
    # --- Police (kept split by sub-type per your call) ---
    'Airport Police': "Airport Police Department",
    'Transit Police': "Transit Police Department",
    'University PD': "University Police Department",
    'Campus Police': "Campus Police Department",
    'University Police': "University Police Department",
    'College Police': "University Police Department",
    'Virginia Tech Police Department': "University Police Department",
    'Division of Police': "Police Department",
    'Police Services': "Police Department",
    'Police': "Police Department",
    'PD': "Police Department",

    # --- Sheriff / Marshal / Constable ---
    'Sheriffs Office': "Sheriff's Office",
    'Sheriffs': "Sheriff's Office",
    'Sheriff': "Sheriff's Office",
    'SO': "Sheriff's Office",
    'Fire Marshal': "Fire Marshal's Office",
    'Marshals Office': "Marshal's Office",
    'Marshals': "Marshal's Office",
    'Marshal': "Marshal's Office",
    'Constable': "Constable's Office",
    'Const': "Constable's Office",

    # --- State-level law enforcement (merged per your call) ---
    'State Highway Patrol': "State Police",
    'Highway Patrol': "State Police",
    'State Patrol': "State Police",
    'State Police': "State Police",
    'Trooper': "State Police",
    'Bureau of Investigation': "State Bureau of Investigation",
    'Bureau of Criminal Investigation': "State Bureau of Investigation",
    'Division of Criminal Investigation': "State Bureau of Investigation",
    'Criminal Justice' : 'State Bureau of Investigation',
    'KBI': 'State Bureau of Investigation',

    # --- Corrections ---
    'Department of Corrections': "State Department of Corrections",
    'Dept of Corrections': "State Department of Corrections",
    'Department of Correction': "State Department of Corrections",
    'Department of Rehabilitation': "State Department of Corrections",

    # --- Prosecutorial ---
    'District Attorney': "District Attorney's Office",
    'DA': "District Attorney's Office",
    'Attorneys': "District Attorney's Office",
    'Houston County GA District Attorneys Office': "District Attorney's Office",
    'Prosecutors Office': "Prosecutor's Office",
    'Prosecutor Office': "Prosecutor's Office",
    'Prosector': "Prosecutor's Office",
    'County Attorney': "County Attorney's Office",
    'Kleberg TX County Attorneys Task Force': "County Attorney's Office",
    'Attorney General': "Attorney General's Office",
    'Attorney Generals Office': "Attorney General's Office",

    # --- Public safety / federal / postal ---
    'Department of Public Safety': "Department of Public Safety",
    'Public Safety': "Department of Public Safety",
    'Pub Safety': "Department of Public Safety",
    'DPS': "Department of Public Safety",
    'PSD': "Department of Public Safety",
    'Federal': "Federal Agency",
    'Postal': "United States Postal Service",
    'USPS': "United States Postal Service",

    # --- Drugs / narcotics ---
    'Narcotics': "Narcotics Division/Drug Enforcement",
    'Drug Enforcement': "Narcotics Division/Drug Enforcement",
    'HIDTA': "Narcotics Division/Drug Enforcement",
    'Indiana HIDTA': "Narcotics Division/Drug Enforcement",
    'RIG WI DTF': "Narcotics Division/Drug Enforcement",
    'Drug Task Force': "Narcotics Division/Drug Enforcement",

    # --- Intelligence / regional crime analysis ---
    'Fusion Center': 'Regional Crime Analysis',
    'Analysis Center': 'Regional Crime Analysis',
    'Intelligence Unit': 'Regional Crime Analysis',
    'Information': 'Regional Crime Analysis',
    'RIIC': 'Regional Crime Analysis',
    'GA  MCSOCUIntelligence': 'Regional Crime Analysis',
    'NESPIN  New England State Police Information Network': 'Regional Crime Analysis',
    'MOCIC': 'Regional Crime Analysis',
    'TN ROCIC': 'Regional Crime Analysis',
    'Texas Financial Crimes Intelligence Center': 'Regional Crime Analysis',
    'Antigang': 'Regional Crime Analysis',
    'MAGLOCLEN RISS': 'Regional Crime Analysis',
    'SEMRECC MA':'Regional Crime Analysis',

    # --- Transportation ---
    'Department of Transportation': "Department of Transportation",
    'Motor Vehicles' : 'Department of Motor Vehicles',
    'DOT': "Department of Transportation",
    'Auto Theft': "Auto Theft Division",
    'Vehicle Burglary': "Auto Theft Division",
    'Transit': 'Local Transit Authority',

    # --- Government / administrative ---
    'County Commission': "County Commission",
    'Commissioner': "County Commission",
    'Communications': "Communications/Dispatch",
    'Dispatch': "Communications/Dispatch",
    '911': "Communications/Dispatch",
    'Inspector General': "Inspector General",
    'Workers Compensation': "Workers Compensation Office",
    'Major Crimes': "Major Crimes Division",
    'Criminal Taskforce': "Law Enforcement Agency",
    'Law Enforcement': "Law Enforcement Agency",

    # --- Other state/regulatory agencies ---
    'Deparment of Revenue': "Department of Revenue",
    'Alabama Department of Revenue': "Department of Revenue",
    'Department of Wildlife': "Department of Wildlife",
    'Department of Justice': "Department of Justice",
    'Natural Resources': "Department of Natural Resources",
    'Insurance Fraud': "Department of Insurance Fraud",
    'Environmental Health': "Department of Environmental Health",
    'Conservation': "State Conservation Department",
    'OK  477': 'Indigenous Peoples Support',

    # --- Facilities / misc org types ---
    'Parks': "Parks Department",
    'Park': "Parks Department",
    'Metroparks': "Parks Department",
    'Housing': "Housing Authority",
    'Circuit': "Circuit Court",
    'Academy': "Unspecified Educational Department",
    'Schools': "School District",
    'School': "School District",
    'ISD': 'School District',
    'University': "Unknown University Department",
    'College': "Unknown University Department",
    'Airport': "Unknown Airport Department",
    'Fire': "Fire Department",
    'Arson': "Arson Division",

    # --- Unspecified / catch-all placeholders ---
    'City of': "Unspecified Local Government Department",
    'Township': "Unspecified Local Government Department",
    'Town of': "Unspecified Local Government Department",
    'Hamilton GA': "Unspecified Local Government Department",
    'Hilton Head Island SC': "Unspecified Local Government Department",
    'UCPAO AR': "Unknown Organization",
    'National Center for Missing  Exploited Children NCMEC': "National Organization",
    'County': 'Unspecified Local Government Department',
    'City': 'Unspecified Local Government Department',
    'Task Force' :  "Unspecified Local Government Department",
    'Village' :  "Unspecified Local Government Department",
    'Twp' : "Unspecified Local Government Department",



}

# Sort keys longest-first so more specific multi-word phrases (e.g.
# "University PD") are checked before shorter ones they contain (e.g. "PD").
ORG_TYPE_KEYS_BY_LENGTH = sorted(ORG_TYPES.keys(), key=len, reverse=True)

STATE_NAMES = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
    'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
    'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
    'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
    'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
    'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH',
    'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC',
    'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA',
    'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC', 'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN',
    'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA',
    'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY', 'Savannah': 'GA', 
    'Fort Collins': 'CO','Gwinnett County': 'GA', 'Memphis': 'TN', 'National': 'DC', 
    'Federal': 'DC', 'NYS':'NY', 'Louiseville': 'KY', 'MOCIC': 'MO','NESPIN': 'MA','Louisville': 'KY',
    'Niagara Frontier Transit Authority NFTA PD':'NY','Orleans':'LA', 'Tupelo':'MS', 'Griffin': 'GA', 'chesapeake':'VA',
    'CSX': 'VA','Edison State': 'OH','ChathamSavannah Counter Narcotics Team':'GA',
    'Harrisonburg':'VA','Harrisonburg-Rockingham':'VA','Harrisonburg-Rockingham Regional':'VA',
}    
STATE_NAME_KEYS_BY_LENGTH = sorted(STATE_NAMES.keys(), key=len, reverse=True)


def extract_state(cleaned_name):
    """
    Given the cleaned org name STRING, return a two-letter state
    abbreviation. Checks full state names first (e.g. "South Carolina",
    "New York") using word-boundary regex so multi-word names match
    correctly, then falls back to checking each word against the set of
    two-letter abbreviations. Returns None if nothing matches.
    """
    if not isinstance(cleaned_name, str):
        return None

    for name_key in STATE_NAME_KEYS_BY_LENGTH:
        pattern = r'\b' + re.escape(name_key) + r'\b'
        if re.search(pattern, cleaned_name, flags=re.IGNORECASE):
            return STATE_NAMES[name_key]

    for word in cleaned_name.split():
        if word.upper() in STATE_ABBRS:
            return word.upper()

    return None


def extract_org_type(cleaned_name):

    if not isinstance(cleaned_name, str):
        return None

    for key in ORG_TYPE_KEYS_BY_LENGTH:
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, cleaned_name, flags=re.IGNORECASE):
            return ORG_TYPES[key]

    # Special case: DA / DAs / DA's (Office)
    if re.search(r"\bDA'?s?\b", cleaned_name, flags=re.IGNORECASE):
        return "District Attorney"

    return None


def main():

    orgs['Org Name Cleaned'] = orgs['Org Name'].str.strip()
    orgs['Org Name Cleaned'] = orgs['Org Name Cleaned'].str.replace(r'[^a-zA-Z0-9 ]', '', regex=True)

    print(orgs['Org Name Cleaned'].head(30))

    orgs['State'] = orgs['Org Name Cleaned'].apply(extract_state)
    orgs['Org Type'] = orgs['Org Name Cleaned'].apply(extract_org_type)

    orgs.to_csv(OUTPUT_PATH, index=False)


if __name__ == '__main__':
    main()


# %%


print(orgs['Org Type'].value_counts())

# %%

orgs  = pd.read_csv('Flock_Network_Sharing_Lists_6-15-2026_cleaned.csv')

print(grouped.columns)

print(orgs.columns)

df_full = grouped.merge(orgs[['Org Name', 'State', 'Org Type']], how='left', left_on='Org_Name', right_on='Org Name')
print(df_full.info())

print(df_full['Count'].sum())


pd_audit = pd.read_csv(r"1_25-5_26-Combined_PD-Audit.csv")
pd_audit.columns = pd_audit.columns.str.strip()
print(pd_audit.columns)
print(df_full.columns)

#start of reason categorization

import re
from collections import Counter
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------
# 0. Build the deduped raw-reasons file from your two audit sources
# ---------------------------------------------------------------------

DISTINCT_REASONS_CSV = "distinct_reasons.csv"   # what main() will read/classify
OUTPUT_CSV = "reason_category_mapping.csv"      # raw_reason, case_number, category

# df_full already exists in memory from your earlier merge step
#raw_reasons = pd.concat(
#    [df_full[['Reason', 'Case #']], pd_audit[['Reason', 'Case #']]],
#    ignore_index=True,
#).drop_duplicates()

raw_reasons = df_full[['Reason','Case #']].drop_duplicates()

print(raw_reasons.info())

raw_reasons.to_csv(DISTINCT_REASONS_CSV, index=False)
# ---------------------------------------------------------------------
# 1. Canonical categories + ordered regex rules.
#    Add / reorder as you inspect the "Other/Uncategorized" bucket.
# ---------------------------------------------------------------------

CATCHALL = "Other / Uncategorized"
UNKNOWN = "Other / Uncategorized"
INVESTIGATION = "Investigation / Case Follow-up (generic)"

RULES: list[tuple[str, re.Pattern]] = [
    ("Wanted Person / Warrant", re.compile(
        r"\bwarrant\b|\bwanted\b|\bfugitive\b|\bfelony pick ?up\b|\babscond", re.I)),

    ("Homicide / Death Investigation", re.compile(
        r"\bhomicide\b|\bmurder\b|\bdeath invest|\bdeceased\b|\bhom\b", re.I)),

    ("Kidnapping / Abduction", re.compile(
        r"\bkidnap|\babduct", re.I)),

    ("Human Trafficking", re.compile(
        r"\bhuman traffic|\bht\b(?!v)|\btrafficking.{0,10}(minor|child|person)", re.I)),

    ("Weapons / Shots Fired", re.compile(
        r"\bshots? fired\b|\bshooting\b|\bfirearm\b|\bgun\b|\bgsw\b|\bweapon\b|"
        r"\bagg(ravated)? assault\b.*(gun|weapon|deadly)", re.I)),

    ("Robbery", re.compile(
        r"\brobbery\b|\barmed robbery\b|\bjugging\b|\bcarjack", re.I)),

    ("Assault / Battery", re.compile(
        r"\bassault\b|\bbattery\b|\bstabbing\b|\bdomestic (violence|battery|assault)\b|"
        r"\bagg ?ass(ault)?\b|\bdv\b|10-40|1040", re.I)),

    ("Sex Offenses", re.compile(
        r"\bsex offen|\brape\b|\bmolest|\bicac\b|\bcsam\b|\bindecent exposure\b|"
        r"\bsexual (assault|battery)\b", re.I)),

    ("Burglary / Breaking & Entering", re.compile(
        r"\bburglary\b|\bbreak(ing)? ?(and|&)? ?enter|\bb ?& ?e\b|\bentering auto|\bburg", re.I)),

    ("Motor Vehicle Theft / Stolen Vehicle", re.compile(
        r"\bstolen (vehicle|car|auto|truck|motorcycle|trailer|plate|tag)\b|"
        r"\bveh(icle)? theft\b|\bauto theft\b|\bgtmv\b|\budaa\b|\bmvt\b|\bcarjack", re.I)),

    ("Stolen Property (non-vehicle)", re.compile(
        r"\bstolen (property|item|goods|firearm|gun|package|equipment)\b|"
        r"\breceiving stolen property\b", re.I)),

    ("Larceny / Theft", re.compile(
        r"\blarceny\b|\btheft\b|\bshoplift|\bretail theft\b|\bstolen\b", re.I)),

    ("Financial Crime / Fraud", re.compile(
        r"\bfraud\b|\bembezzl|\bforgery\b|\bcounterfeit|\bidentity theft\b|"
        r"\bskimm|\bcredit card\b", re.I)),

    ("Drugs / Narcotics", re.compile(
        r"\bdrug\b|\bnarcotic|\bmeth\b|\bcocaine\b|\bheroin\b|\bfentanyl\b|"
        r"\bdtf\b|\bhidta\b", re.I)),

    ("Missing / Endangered Person", re.compile(
        r"\bmissing\b|\bendangered\b|\brunaway\b|\bsilver alert\b|\bamber alert\b|"
        r"\bwelfare (check|concern)\b|\bwelf\b", re.I)),

    ("Hit and Run / Car Accident", re.compile(
        r"\bhit and run\b|\bhit ?[/-]? ?skip\b|\baccident\b|\bcrash\b|\bmva\b|\bcollision\b",
        re.I)),

    ("DUI / Impaired Driving", re.compile(
        r"\bdui\b|\bdwi\b|\bowi\b|\bovi\b|\bintoxicated\b", re.I)),

    ("Fleeing / Eluding Police", re.compile(
        r"\bflee(ing)?\b|\belud|\bpursuit\b", re.I)),

    ("Traffic Infraction", re.compile(
        r"\btraffic\b|\bspeeding\b|\breckless driving\b|\bno insurance\b|"
        r"\bsuspended (license|dl|plate)\b|\bexpired (tag|reg)", re.I)),

    ("Arson / Fire", re.compile(
        r"\barson\b|\bfire investigation\b", re.I)),

    ("Illegal Dumping / Littering", re.compile(
        r"\bdumping\b|\blittering\b", re.I)),

    ("Vandalism / Property Damage", re.compile(
        r"\bvandalism\b|\bcriminal damage\b|\bdestruction of property\b", re.I)),

    ("Trespass", re.compile(r"\btrespass", re.I)),

    ("Animal Offenses", re.compile(r"\banimal\b", re.I)),

    ("Terrorism / Threats", re.compile(
        r"\bterror|\bbomb threat\b|\bthreat(s|ening)?\b", re.I)),

    ("Protective / Protection Order", re.compile(
        r"\bprotective order\b|\bprotection order\b|\btpo\b|\brestraining order\b", re.I)),

    ("Investigation / Case Follow-up (generic)", re.compile(
        r"\binvestigat|\bcase\b|\bfollow[- ]?up\b|\bfup\b|\binv|\binvest", re.I)),

    ("Testing / Training / Admin", re.compile(
        r"\btest\b|\btraining\b|\bdemo\b|\badmin\b|\bpractice\b", re.I)),
]


def normalize(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def has_case_number(case_number) -> bool:
    """True if case_number is a real, non-empty value (handles pandas NaN too)."""
    if case_number is None or pd.isna(case_number):
        return False
    s = str(case_number).strip()
    return s != "" and s.lower() != "nan"


def reason_contains_case_number(reason) -> bool:
    """
    Detect a case number embedded inside the free-text Reason field itself
    (separate from a dedicated Case # column). Treated as a case number if:
      - the text contains a '#' character, OR
      - the text starts with '25' and is more than 3 characters long
        (e.g. a 2025-prefixed case number like '25-001234').
    """
    if not isinstance(reason, str):
        return False
    text = reason.strip()
    if '#' in text:
        return True
    if text.startswith('25') and len(text) > 3:
        return True
    return False


def classify(raw: str, case_number=None) -> str:
    """
    Classify a raw reason string into a category.

    A populated Case # column, OR a case number embedded in the Reason
    text itself, always wins and forces INVESTIGATION. Otherwise, falls
    through to the regex RULES, then UNKNOWN for too-short text, then
    CATCHALL if nothing matched.
    """
    if has_case_number(case_number) or reason_contains_case_number(raw):
        return INVESTIGATION

    text = normalize(raw) if isinstance(raw, str) else ""
    if len(text) < 2:
        return UNKNOWN

    for category, pattern in RULES:
        if pattern.search(text):
            return category

    return CATCHALL


def main():
    in_path = Path(DISTINCT_REASONS_CSV) #save reasons as separate csv file for easy mapping of several million rows down the line
    if not in_path.exists():
        print(
            f"'{DISTINCT_REASONS_CSV}' not found. Run the preprocessing step "
            f"above first to generate it, then re-run."
        )
        return

    df = pd.read_csv(in_path)

    if "Reason" not in df.columns:
        raise ValueError(f"Expected a 'Reason' column in {DISTINCT_REASONS_CSV}, got: {list(df.columns)}")

    has_case_number_col = "Case #" in df.columns

    df["Category"] = df.apply(
        lambda row: classify(
            row["Reason"],
            row["Case #"] if has_case_number_col else None,
        ),
        axis=1,
    )

    # Keep a row if it has real Reason text, OR a real Case # value,
    # OR an embedded case number pattern inside the Reason text itself.
    keep_mask = df["Reason"].notna() & (df["Reason"].astype(str).str.strip() != "")
    if has_case_number_col:
        keep_mask = keep_mask | df["Case #"].apply(has_case_number)
    keep_mask = keep_mask | df["Reason"].apply(reason_contains_case_number)
    df = df[keep_mask]

    output_cols = ["Reason"] + (["Case #"] if has_case_number_col else []) + ["Category"]
    df[output_cols].to_csv(OUTPUT_CSV, index=False)

    counts = Counter(df["Category"])
    print(f"Classified {len(df)} rows -> {OUTPUT_CSV}\n")
    for cat, n in counts.most_common():
        print(f"{n:6d}  {cat}")


if __name__ == "__main__":
    main()

reason = pd.read_csv('reason_category_mapping.csv')

reason_categories = reason[['Reason', 'Case #', 'Category']]
df_full = df_full.merge(reason_categories, on=['Reason', 'Case #'], how='left')


pd.set_option('display.max_rows', None)


mask = df_full['Text Prompt'].str.contains('objectClass:people', na=False)
people = df_full[mask]

print(people['Text Prompt'].value_counts())

pd_audit = pd_audit.merge(reason_categories, on=['Reason', 'Case #'], how='left')



# Step 1: Parse the column to datetime (strip " UTC" suffix first)
#pd_audit['Search Time'] = pd_audit['Search Time'].str.replace(" UTC", "", regex=False)

# Step 2: Parse with format='mixed' so pandas infers per-row, and utc=True so
# everything becomes UTC-aware in one step (handles the naive "UTC"-suffixed
# rows AND the already-offset-aware ISO rows correctly, without a separate
# tz_localize step that would fail on already-aware timestamps)

pd_audit['Search Time'] = pd.to_datetime(pd_audit['Search Time'], format='mixed', utc=True)

# Step 3: Convert to Eastern
pd_audit['Search Time'] = pd_audit['Search Time'].dt.tz_convert("America/New_York")


# Step 3: Split into separate date and time columns
pd_audit['Search Date'] = pd_audit['Search Time'].dt.strftime("%m/%d/%Y")
pd_audit['Search_Time'] = pd_audit['Search Time'].dt.strftime("%I:%M:%S %p")

print(pd_audit[['Search Date', 'Search_Time']].head())


split_cols = pd_audit['Time Frame'].str.split('\n', expand=True)

pd_audit['Start Time'] = split_cols[0]
pd_audit['End Time'] = split_cols[1]

# Step 1: Parse the column to datetime (strip " UTC" suffix first)
pd_audit['Start Time'] = pd_audit['Start Time'].str.replace(" UTC", "", regex=False)
pd_audit['End Time'] = pd_audit['End Time'].str.replace(" UTC", "", regex=False)
pd_audit['Start Time'] = pd.to_datetime(pd_audit['Start Time'], format="%m/%d/%Y, %I:%M:%S %p")
pd_audit['End Time'] = pd.to_datetime(pd_audit['End Time'], format="%m/%d/%Y, %I:%M:%S %p")

# Step 2: Localize as UTC, then convert to Eastern
pd_audit['Start Time'] = pd_audit['Start Time'].dt.tz_localize("UTC").dt.tz_convert("America/New_York")
pd_audit['End Time'] = pd_audit['End Time'].dt.tz_localize("UTC").dt.tz_convert("America/New_York")

pd_audit['Search Time Frame (Days)'] = pd_audit['End Time'] - pd_audit['Start Time']

print(pd_audit[['Start Time', 'End Time', 'Search Time Frame (Days)']].head())



pa = pd_audit.filter(['ID', 'Name', 'Org Name', 'Total Networks Searched',
       'Time Frame', 'License Plate', 'Reason', 'Case #', 'Filters',
       'Search Time', 'Search Type', 'Text Prompt', 'Moderation', 'Category_x',
       'Search Date', 'Search_Time', 'Start Time', 'End Time', 'Search Time Frame (Days)'])

pa['Reason Category'] = pa['Category_x']
pa['Search Time Frame Start'] = pa['Start Time']
pa['Search Time Frame End'] = pa['End Time']

print(pa['Name'].value_counts())

pa = pa.filter(['ID', 'Name', 'Org Name', 'Total Networks Searched',
       'Time Frame', 'License Plate', 'Reason', 'Case #', 'Filters',
       'Search Time', 'Search Type', 'Text Prompt', 'Moderation', 'Reason Category',
       'Search Date', 'Search_Time', 'Search Time Frame Start', 'Search Time Frame End', 'Search Time Frame (Days)'])


print(pa.columns)

pa.to_csv(r'~\1_25-5_26-Combined_PD-Audit_v2.csv')


#end of pd_audit processing, file uploaded to dropbox for pulling into Streamlit app

df = df.groupby(['Search Time Frame (Days)','Search Date',
        'Search Hour', 'Org Name', 'State', 'Org Type', 'Category'],dropna=False)[['Networks', 'Count']].sum().reset_index()

print(df['Count'].sum())



print(f"Original rows: {len(df):,}")
print(f"Aggregated rows: {len(df):,}")
print(f"File size: {df.memory_usage(deep=True).sum() / 1_000_000:.1f} MB in memory")


network_agg = df.groupby(["Org Name", "State", "Org Type", "Category", "Search Time Frame (Days)"], dropna=False)[["Networks", "Count"]].sum().reset_index()


network_agg = network_agg[~network_agg['Org Name'].str.contains('dekalb', case=False, na=False)]


print(network_agg['Count'].sum())



network_agg.to_parquet('aggregated.parquet', compression='snappy')


