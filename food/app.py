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
    if not os.path.exists('model_xgb.pkl') or not os.path.exists('model_reg.pkl'):
        return None, None
    
    try:
        model_class = joblib.load('model_xgb.pkl')
        model_reg = joblib.load('model_reg.pkl')
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
    # Safety Check: If mass is 0, we cannot calculate density
    if total_mass == 0: 
        return None, None
    
    sugar_fiber_ratio = sugar / fiber if fiber > 0 else 0.0

    data = pd.DataFrame([{
        'Calorie_Density': predicted_cals / total_mass,
        'Fat_Density': fat / total_mass,
        'Sugar_Density': sugar / total_mass,
        'Protein_Density': protein / total_mass,
        'Fiber_Density': fiber / total_mass,
        'Saturated_Fat_Density': sat_fat / total_mass,
        'Cholesterol_Density': cholesterol / total_mass,
        'Water_Density': water / total_mass,
        'Sugar_Fiber_Ratio': sugar_fiber_ratio,
        'Sodium_Density': sodium / total_mass
    }])

    prediction = model_class.predict(data)[0]
    prob_healthy = model_class.predict_proba(data)[0][1]
    
    return prediction, prob_healthy

# --- 4. MAIN APP UI ---
def main():
    # --- SIDEBAR INSTRUCTIONS ---
    with st.sidebar:
        st.header("📘 Instructions")
        st.info("""
        **Navigation Tip:**
        Press **TAB** to switch boxes.
        (Pressing **Enter** will submit the form!)
        """)
        st.markdown("""
        1. **Enter Data:** Type the nutrients.
        2. **Analyze:** Click the button below.
        """)

    st.title("AI Nutritionist")
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

        st.write("#### Macro Nutrients (Press TAB to switch)")
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
        # 1. Calculate Mass & Calories FIRST
        predicted_calories = predict_calories(model_reg, fat, carbs, protein, fiber)
        total_mass = fat + carbs + protein + water + (sodium/1000) + (cholesterol/1000)
        
        # 2. SAFETY CHECK: Did the user enter data?
        if total_mass == 0:
            st.warning("Please enter some nutrient values before analyzing.")
        else:
            with st.spinner("AI is crunching the numbers..."):
                prediction, prob_healthy = analyze_health(
                    model_class, predicted_calories, total_mass,
                    fat, sugar, protein, fiber, sodium, sat_fat, cholesterol, water
                )

                # If analyze_health returns None (double check)
                if prediction is None:
                    st.error("Error calculating health score.")
                else:
                    st.divider()
                    st.header(f"Results for: {name if name else 'Food Item'}")

                    m1, m2, m3 = st.columns(3)
                    m1.metric("AI Calculated Calories", f"{predicted_calories:.0f} kcal")
                    m2.metric("Total Mass", f"{total_mass:.1f} g")
                    
                    if prediction == 1:
                        verdict = "HEALTHY"
                        conf_score = prob_healthy
                        color_box = st.success
                    else:
                        verdict = "UNHEALTHY"
                        # FIX: Handle cases where prob_healthy is None
                        if prob_healthy is not None:
                            conf_score = 1 - prob_healthy
                        else:
                            conf_score = 0.0
                        color_box = st.error

                    m3.metric("Confidence", f"{conf_score:.1%}")
                    color_box(f"## Verdict: {verdict}")

if __name__ == "__main__":
    main()