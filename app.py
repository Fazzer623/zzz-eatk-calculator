import streamlit as st

# === Calculator functions ===

def calculate_eatk(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff):
    """Calculate Effective ATK (EATK) given inputs."""
    final_atk = initial_atk * (1 + combat_atk_buff/100) + flat_atk_buff
    cr_capped = min(cr / 100, 1.0)
    cd_decimal = cd / 100
    return final_atk * (1 + cr_capped * cd_decimal)

def add_atk_roll(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, atk_roll_value):
    """Add one ATK% roll to Initial ATK and recalc EATK."""
    new_initial = initial_atk + atk_roll_value
    return calculate_eatk(new_initial, cr, cd, flat_atk_buff, combat_atk_buff)

def add_cr_roll(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, cr_roll_value=2.4):
    """Add one CR% roll and recalc EATK."""
    new_cr = cr + cr_roll_value
    return calculate_eatk(initial_atk, new_cr, cd, flat_atk_buff, combat_atk_buff)

def add_cd_roll(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, cd_roll_value=4.8):
    """Add one CD% roll and recalc EATK."""
    new_cd = cd + cd_roll_value
    return calculate_eatk(initial_atk, cr, new_cd, flat_atk_buff, combat_atk_buff)

def optimize_substats(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, atk_roll_value, cr_roll_value=2.4, cd_roll_value=4.8, max_iterations=100):
    current_cr = cr
    current_cd = cd
    current_initial = initial_atk

    def step_increases(iatk, icr, icd):
        base = calculate_eatk(iatk, icr, icd, flat_atk_buff, combat_atk_buff)
        inc_atk = calculate_eatk(iatk + atk_roll_value, icr, icd, flat_atk_buff, combat_atk_buff) - base
        inc_cr = calculate_eatk(iatk, icr + cr_roll_value, icd, flat_atk_buff, combat_atk_buff) - base
        inc_cd = calculate_eatk(iatk, icr, icd + cd_roll_value, flat_atk_buff, combat_atk_buff) - base
        return inc_atk, inc_cr, inc_cd

    for _ in range(max_iterations):
        inc_atk, inc_cr, inc_cd = step_increases(current_initial, current_cr, current_cd)

        increments = {'atk': inc_atk, 'cr': inc_cr, 'cd': inc_cd}
        max_key = max(increments, key=increments.get)
        min_key = min(increments, key=increments.get)

        if abs(increments[max_key] - increments[min_key]) < 1e-6:
            break

        # Moves must respect lower bounds:
        if min_key == 'atk' and max_key == 'cr':
            current_initial -= atk_roll_value
            current_cr = min(current_cr + cr_roll_value, 100)
        elif min_key == 'atk' and max_key == 'cd':
            current_initial -= atk_roll_value
            current_cd = max(current_cd + cd_roll_value, 50)  # lower bound 50%
        elif min_key == 'cr' and max_key == 'atk':
            if current_cr - cr_roll_value >= 5:  # lower bound 5%
                current_initial += atk_roll_value
                current_cr -= cr_roll_value
        elif min_key == 'cr' and max_key == 'cd':
            if current_cr - cr_roll_value >= 5:
                current_cr -= cr_roll_value
                current_cd = max(current_cd + cd_roll_value, 50)
        elif min_key == 'cd' and max_key == 'atk':
            if current_cd - cd_roll_value >= 50:
                current_initial += atk_roll_value
                current_cd -= cd_roll_value
        elif min_key == 'cd' and max_key == 'cr':
            if current_cd - cd_roll_value >= 50:
                current_cd -= cd_roll_value
                current_cr = min(current_cr + cr_roll_value, 100)

        # Clamp CR and CD to boundaries after all moves:
        current_cr = max(min(current_cr, 100), 5)
        current_cd = max(current_cd, 50)
        current_initial = max(current_initial, 0)

    optimized = {
        'initial_atk': current_initial,
        'cr': current_cr,
        'cd': current_cd,
        'EATK': calculate_eatk(current_initial, current_cr, current_cd, flat_atk_buff, combat_atk_buff)
    }
    return optimized
# === Streamlit UI ===

st.title("EATK Calculator & Optimizer")

st.markdown("""
Enter your character stats below.  
Percentage values are in **% (0-100)** for easier input.
""")

initial_atk = st.number_input("Initial ATK (Stat screen value)", min_value=0.0, value=2900.0, step=1.0, format="%.1f")

cr = st.number_input("Combat Critical Rate (CR %) (0 to 100)", min_value=0.0, max_value=100.0, value=80.0, step=0.1, format="%.2f")

cd = st.number_input("Combat Critical Damage (CD %) (e.g. 160 for 160%)", min_value=0.0, value=160.0, step=0.1, format="%.2f")

flat_atk_buff = st.number_input("Flat ATK Buff (from external sources)", value=200.0, step=1.0, format="%.1f")

combat_atk_buff = st.number_input("Combat ATK% Buff (as %, e.g. 25 for 25%)", min_value=0.0, value=25.0, step=0.1, format="%.2f")

atk_roll_value = st.number_input("ATK% Substat Roll value (added to Initial ATK)", min_value=0.0, value=49.26, step=0.01, format="%.2f")

cr_roll_value = 2.4  # 2.4%
cd_roll_value = 4.8  # 4.8%

if st.button("Optimize"):

    base_eatk = calculate_eatk(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff)
    st.write(f"**Base EATK:** {base_eatk:.2f}")

    eatk_atk_roll = add_atk_roll(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, atk_roll_value)
    inc_atk = eatk_atk_roll - base_eatk
    st.write(f"Add 1 ATK% roll (+{atk_roll_value:.1f} ATK): EATK = {eatk_atk_roll:.2f} (+{inc_atk:.2f}, +{inc_atk/base_eatk*100:.2f}%)")

    eatk_cr_roll = add_cr_roll(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, cr_roll_value)
    inc_cr = eatk_cr_roll - base_eatk
    st.write(f"Add 1 CR% roll (+{cr_roll_value:.1f}% CR): EATK = {eatk_cr_roll:.2f} (+{inc_cr:.2f}, +{inc_cr/base_eatk*100:.2f}%)")

    eatk_cd_roll = add_cd_roll(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, cd_roll_value)
    inc_cd = eatk_cd_roll - base_eatk
    st.write(f"Add 1 CD% roll (+{cd_roll_value:.1f}% CD): EATK = {eatk_cd_roll:.2f} (+{inc_cd:.2f}, +{inc_cd/base_eatk*100:.2f}%)")

    optimized = optimize_substats(initial_atk, cr, cd, flat_atk_buff, combat_atk_buff, atk_roll_value, cr_roll_value, cd_roll_value)

    st.markdown("---")
    st.write("### Optimized stats for balanced roll value:")

    st.write(f"Initial ATK: {optimized['initial_atk']:.2f}")
    st.write(f"CR: {optimized['cr']:.2f} %")
    st.write(f"CD: {optimized['cd']:.2f} %")
    st.write(f"EATK: {optimized['EATK']:.2f}")

    inc_atk_opt, inc_cr_opt, inc_cd_opt = (
        add_atk_roll(optimized['initial_atk'], optimized['cr'], optimized['cd'], flat_atk_buff, combat_atk_buff, atk_roll_value) - optimized['EATK'],
        add_cr_roll(optimized['initial_atk'], optimized['cr'], optimized['cd'], flat_atk_buff, combat_atk_buff, cr_roll_value) - optimized['EATK'],
        add_cd_roll(optimized['initial_atk'], optimized['cr'], optimized['cd'], flat_atk_buff, combat_atk_buff, cd_roll_value) - optimized['EATK'],
    )

    st.write("#### Step increases at optimized stats:")
    st.write(f"Add 1 ATK% roll: +{inc_atk_opt:.2f} (+{inc_atk_opt/optimized['EATK']*100:.3f}%)")
    st.write(f"Add 1 CR% roll: +{inc_cr_opt:.2f} (+{inc_cr_opt/optimized['EATK']*100:.3f}%)")
    st.write(f"Add 1 CD% roll: +{inc_cd_opt:.2f} (+{inc_cd_opt/optimized['EATK']*100:.3f}%)")
