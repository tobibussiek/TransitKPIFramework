# Headway regularity under each snapshot rule, next to the OTP swing.
# Question: is headway as choice-dependent as OTP, or more robust to it?
# closest pulls each arrival toward its evenly-spaced scheduled slot, so it
# regularizes headways the same way it biases OTP; latest is the realized proxy;
# last_before drops stop events with no pre-schedule snapshot, so its chains have
# gaps and it is the least trustworthy here. Anchor on closest vs latest.

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(r'C:\Users\Tobi\Desktop\CSHW\TransitKPIFramework')
DB_PATH      = PROJECT_ROOT / 'data' / 'transit_kpi.duckdb'
con = duckdb.connect(str(DB_PATH))

# High-frequency daytime window only (06:00-21:00); headway regularity isn't
# meaningful where service is sparse. Match the weekday scope from notebook 04.
HF_START_SEC = 21600
HF_END_SEC   = 75600
MAX_SCHED_HEADWAY_MIN  = 20.0   # keep cells in the high-frequency regime
ACTUAL_HEADWAY_CAP_MIN = 60.0   # drop feed-gap / dropped-trip artifacts

snapshot_tables = {
    'closest':     'trip_delays_closest',
    'last_before': 'trip_delays_last_before',
    'latest':      'trip_delays_latest',
}


def awt(headways):
    # average wait for random passenger arrivals: sum(H^2) / (2*sum(H))
    h = np.asarray(headways, dtype=float)
    return (h ** 2).sum() / (2.0 * h.sum())


def headway_by_route(table):
    # one realized arrival per stop event under this rule; difference consecutive
    # buses at the same stop to get actual headways, scheduled times for the baseline
    ev = con.sql(f"""
        SELECT route_id, direction_id, service_date, stop_id, trip_id,
               predicted_unix, scheduled_unix, scheduled_arrival_seconds
        FROM {table}
        WHERE ISODOW(CAST(service_date AS DATE)) BETWEEN 1 AND 5
          AND scheduled_arrival_seconds >= {HF_START_SEC}
          AND scheduled_arrival_seconds <  {HF_END_SEC}
    """).df()

    grp = ['route_id', 'direction_id', 'service_date', 'stop_id']

    ev_a = ev.sort_values(grp + ['predicted_unix']).copy()
    ev_a['actual_headway_min'] = ev_a.groupby(grp)['predicted_unix'].diff() / 60.0
    ev_s = ev.sort_values(grp + ['scheduled_unix']).copy()
    ev_s['scheduled_headway_min'] = ev_s.groupby(grp)['scheduled_unix'].diff() / 60.0

    sched = (ev_s.dropna(subset=['scheduled_headway_min'])
                 .loc[lambda d: (d['scheduled_headway_min'] > 0) &
                                (d['scheduled_headway_min'] <= MAX_SCHED_HEADWAY_MIN)])
    actual = (ev_a.dropna(subset=['actual_headway_min'])
                  .loc[lambda d: (d['actual_headway_min'] > 0) &
                                 (d['actual_headway_min'] <= ACTUAL_HEADWAY_CAP_MIN)])
    # keep actual headways only at cells that are genuinely high-frequency
    actual = actual.merge(sched[grp].drop_duplicates(), on=grp, how='inner')

    out = {}
    for rt in ['23', '47']:
        a = actual.loc[actual['route_id'] == rt, 'actual_headway_min']
        s = sched.loc[sched['route_id'] == rt, 'scheduled_headway_min']
        awt_a, awt_s = awt(a), awt(s)
        out[rt] = {'n': len(a), 'mean': round(a.mean(), 2),
                   'cv': round(a.std() / a.mean(), 3),
                   'ewt': round(awt_a - awt_s, 2)}
    return out


rows = []
for rule, table in snapshot_tables.items():
    for rt, m in headway_by_route(table).items():
        rows.append({'snapshot_rule': rule, 'route_id': rt, **m})
hw = pd.DataFrame(rows)

print('Headway regularity by snapshot rule and route (weekday 06:00-21:00):')
print(hw.to_string(index=False))

# How far does headway move across the three rules? closest should look most
# regular (lower CV/EWT); if the whole range is small, headway is the robust metric
print()
print('Headway range across the three snapshot rules:')
for rt in ['23', '47']:
    sub = hw[hw['route_id'] == rt]
    cl  = sub[sub.snapshot_rule == 'closest'].iloc[0]
    la  = sub[sub.snapshot_rule == 'latest'].iloc[0]
    print(f"  Route {rt}: CV {sub['cv'].min()}-{sub['cv'].max()}, "
          f"EWT {sub['ewt'].min()}-{sub['ewt'].max()} min; "
          f"closest->latest  CV {cl['cv']}->{la['cv']}, EWT {cl['ewt']}->{la['ewt']} min")

# Same three rules through OTP, for contrast. OTP swings ~30pp here; compare.
print()
print('OTP across the same three rules (reference spec):')
print(con.sql("""
    SELECT snapshot_rule, route_id, otp_pct
    FROM otp_specifications
    WHERE lateness_window = 'neg1_5' AND early_treatment = 'count_early_as_late'
      AND stop_selection = 'all_stops' AND time_of_day = 'all_day'
      AND delay_basis = 'arrival'
    ORDER BY route_id, snapshot_rule
""").df().to_string(index=False))