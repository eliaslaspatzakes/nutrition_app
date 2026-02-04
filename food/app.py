import streamlit as st
import pandas as pd
import joblib
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Nutritionist",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LOAD MODELS ---
@st.cache_resource
def load_models():
   
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    
    class_model_path = os.path.join(current_dir, 'model_xgb.pkl')
    reg_model_path = os.path.join(current_dir, 'model_reg.pkl')

    
    if not os.path.exists(class_model_path) or not os.path.exists(reg_model_path):
        return None, None
    
    try:
        model_class = joblib.load(class_model_path)
        model_reg = joblib.load(reg_model_path)
        return model_class, model_reg
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None
    
# --- 3. LOGIC FUNCTIONS ---
def predict_calories(model_reg, fat, carbs, protein, fiber):
    data = pd.DataFrame([{
        'Fat': fat,
        'Protein': protein,
        'Carbohydrate': carbs,
        'Fiber': fiber
    }])
    # Prevent negative calories if input is empty
    prediction = model_reg.predict(data)[0]
    return max(0, prediction)

def analyze_health(model_class, predicted_cals, total_mass, fat, sugar, protein, fiber, sodium, sat_fat, cholesterol, water):
    if total_mass == 0: 
        return None, None
    
    sugar_fiber_ratio = sugar / fiber if fiber > 0 else 0.0
    
    
    prot_density = protein / total_mass
    sugar_density = sugar / total_mass
    
    data = pd.DataFrame([{
        'Calorie_Density': predicted_cals / total_mass,
        'Fat_Density': fat / total_mass,
        'Sugar_Density': sugar / total_mass,
        'Protein_Density': prot_density,
        'Fiber_Density': fiber / total_mass,
        'Saturated_Fat_Density': sat_fat / total_mass,
        'Cholesterol_Density': cholesterol / total_mass,
        'Water_Density': water / total_mass,
        'Sugar_Fiber_Ratio': sugar_fiber_ratio,
        'Sodium_Density': sodium / total_mass
    }])

    
    prediction = model_class.predict(data)[0]
    prob_healthy = model_class.predict_proba(data)[0][1]
    
    if prediction == 0:
        if (prot_density > 0.15) and (sugar_density < 0.02):
            prediction = 1 
            prob_healthy = 0.85 
            
    return prediction, prob_healthy
def calculate_smart_protein_goal(weight_kg, height_cm, activity_level):
    """
    Calculates protein based on Lean Body Mass approximation.
    If BMI > 25, it adjusts the weight down to prevent over-estimation.
    """
    
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    if bmi > 30:
        
        ideal_weight = 25 * (height_m ** 2)
        
        calculation_weight = ideal_weight + 0.25 * (weight_kg - ideal_weight)
    else:
        
        calculation_weight = weight_kg

    multipliers = {
        "Sedentary (Office Job, No Exercise)": 0.8,
        "Lightly Active (Exercise 1-3 days/week)": 1.2,
        "Moderately Active (Exercise 3-5 days/week)": 1.5,
        "Very Active (Hard Exercise 6-7 days/week)": 1.7,
        "Athlete / Muscle Building (Hypertrophy)": 2.0
    }
    multiplier = multipliers.get(activity_level, 1.2)
    
    return calculation_weight * multiplier, bmi
# --- 4. MAIN APP UI ---
def main():
    # --- SIDEBAR: USER STATS ---
    with st.sidebar:
        st.header("👤 Your Profile")
        st.write("Customize your goals for accuracy.")
        
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.5)
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=175, step=1)
        
        activity = st.selectbox(
            "Activity Level",
            [
                "Sedentary (Office Job, No Exercise)",
                "Lightly Active (Exercise 1-3 days/week)",
                "Moderately Active (Exercise 3-5 days/week)",
                "Very Active (Hard Exercise 6-7 days/week)",
                "Athlete / Muscle Building (Hypertrophy)"
            ],
            index=2
        )
        
        daily_protein_goal, bmi = calculate_smart_protein_goal(weight, height, activity)
        
        st.divider()
        st.metric("Daily Protein Goal", f"{daily_protein_goal:.0f} g")
        
        
        if bmi < 18.5:
            st.caption(f"BMI: {bmi:.1f} (Underweight)")
        elif bmi < 25:
            st.caption(f"BMI: {bmi:.1f} (Normal)")
        elif bmi < 30:
            st.caption(f"BMI: {bmi:.1f} (Overweight)")
        else:
            st.caption(f"BMI: {bmi:.1f} (Obese - Weight Adjusted)")
            st.info("Since BMI is high, we adjusted the protein goal to match your Lean Body Mass, not total weight.")
        
        st.divider()
        st.info("Tip: Press **TAB** to move through the form quickly!")

    st.title("AI Nutritionist")
    st.markdown("### Check if your food is *actually* healthy.")
    st.write("---")

    # Load Models
    model_class, model_reg = load_models()
    if model_class is None:
        st.error("Model files missing! Please check your folder.")
        return

    # --- THE FORM ---
    with st.form("nutrition_form"):
        col_main, col_spacer = st.columns([2, 1])
        with col_main:
            name = st.text_input("Food Name", placeholder="e.g. Greek Yogurt")

        st.write("#### Macro Nutrients")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            fat = st.number_input("Total Fat (g)", min_value=0.0, step=0.1)
        with c2:
            carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.1)
        with c3:
            protein = st.number_input("Protein (g)", min_value=0.0, step=0.1)
        with c4:
            fiber = st.number_input("Fiber (g)", min_value=0.0, step=0.1)

        st.write("#### Micro Nutrients & Details")
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            sugar = st.number_input("Sugar (g)", min_value=0.0, step=0.1)
        with c6:
            sat_fat = st.number_input("Sat. Fat (g)", min_value=0.0, step=0.1)
        with c7:
            sodium = st.number_input("Sodium (mg)", min_value=0.0, step=1.0)
        with c8:
            cholesterol = st.number_input("Cholest. (mg)", min_value=0.0, step=1.0)
        
        st.write("#### Hydration")
        water = st.number_input("Water Content (g)", min_value=0.0, step=1.0)

        st.write("") 
        submitted = st.form_submit_button("ANALYZE FOOD", use_container_width=True, type="primary")

    # --- RESULTS SECTION ---
    if submitted:
        # 1. Calculate Mass & Calories
        predicted_calories = predict_calories(model_reg, fat, carbs, protein, fiber)
        total_mass = fat + carbs + protein + water + (sodium/1000) + (cholesterol/1000)
        
        
        if total_mass == 0:
            st.warning("Please enter some nutrient values before analyzing.")
        else:
            with st.spinner("AI is crunching the numbers..."):
                prediction, prob_healthy = analyze_health(
                    model_class, predicted_calories, total_mass,
                    fat, sugar, protein, fiber, sodium, sat_fat, cholesterol, water
                )

                if prediction is None:
                    st.error("Error calculating health score.")
                else:
                    st.divider()
                    st.header(f"Results for: {name if name else 'Food Item'}")

                    # --- ROW 1: BASIC STATS ---
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Calculated Calories", f"{predicted_calories:.0f} kcal")
                    
                    if prediction == 1:
                        verdict = "HEALTHY"
                        conf_score = prob_healthy
                        color_box = st.success
                    else:
                        verdict = "UNHEALTHY"
                        conf_score = 1 - prob_healthy if prob_healthy is not None else 0.0
                        color_box = st.error

                    m2.metric("AI Verdict", verdict)
                    m3.metric("Confidence", f"{conf_score:.1%}")
                    
                    # --- ROW 2: PROTEIN ANALYSIS ---
                    st.subheader("Protein Analysis")
                    
                    protein_percentage = (protein / daily_protein_goal)
                    bar_progress = min(protein_percentage, 1.0)
                    
                    p_col1, p_col2 = st.columns([3, 1])
                    
                    with p_col1:
                        st.write(f"This food provides **{protein:.1f}g** of protein.")
                        st.progress(bar_progress)
                        st.caption(f"That's **{protein_percentage:.1%}** of your daily goal ({daily_protein_goal:.0f}g).")
                    
                    with p_col2:
                        if protein_percentage >= 0.20:
                            st.success("High Protein!")
                        elif protein_percentage >= 0.10:
                            st.info("Good Source")
                        else:
                            st.write("Low Protein")

if __name__ == "__main__":
    main()