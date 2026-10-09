# 🌿 Invasive Species Risk Assessment Dashboard

A comprehensive web-based assessment tool for evaluating the invasiveness potential of alien plant species using peer-reviewed fuzzy logic models.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool)
[![ResearchGate](https://img.shields.io/badge/ResearchGate-Paper-green)](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)

## 📋 Overview

This dashboard implements scientifically validated fuzzy logic assessment models for evaluating the invasiveness risk of alien plant species. The tool combines:

- **Biological measurements** (quantitative plant traits)
- **Expert knowledge** (qualitative assessments)
- **Fuzzy logic** (to handle uncertainty and imprecision in ecological data)

### 📚 Research Foundation

**Publication:** Novel Fuzzy Linguistic based Mathematical model to assess risk of Invasive alien plant species

- **Journal:** Applied Soft Computing (2017)
- **ResearchGate Link:** [View Full Paper](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)

## ✨ Features

### 🎨 Modern User Interface
- **Professional Design** - Bluish theme with gradient accents
- **Dark Mode Support** - Toggle between light and dark themes
- **Responsive Layout** - Works seamlessly on desktop, tablet, and mobile
- **Interactive Components** - Smooth animations and intuitive controls

### 🔬 Assessment Models

**Model I — LOWA (Equal Weights)**
- Equal weighting for all main risk factors
- Good for baseline assessments
- Simple and balanced approach

**Model II — LWA (Expert Weights)** ⭐ Recommended
- Expert-weighted factors based on scientific evidence
- **Weight Distribution:**
  - Dispersal: 40%
  - Vegetative Reproduction Strength (VRS): 40%
  - Seed Germination Requirement (SGR): 15%
  - Man-made/Natural Disturbance (MIS): 5%
- Highest agreement with real-world data

### 📊 Assessment Factors

#### Dispersal Factors (Quantitative)
Measure how effectively seeds spread:
- **SF** — Seeds per fruit
- **ASR** — Annual seed production per m²
- **VIA** — Seed viability (months)
- **LDD** — Long-distance dispersal potential (0-10 scale)

#### Main Risk Factors (Linguistic)
Assess reproductive capability and human influence:
- **VRS** — Vegetative reproduction strength
- **SGR** — Seed germination requirement level
- **HA** — Human activity influence on spreading
- **NMD** — Natural/man-made disturbance influence

### 🎯 Risk Level Classification

| Risk Level | Description |
|---|---|
| 🟢 **Unlikely** | Extremely low invasiveness potential |
| 🟢 **Very Low** | Very unlikely to become invasive |
| 🔵 **Low** | Low probability of invasion |
| 🟡 **Medium** | Moderate invasiveness risk — monitor closely |
| 🟠 **High** | High invasiveness risk — management recommended |
| 🔴 **Very High** | Very high invasiveness risk — urgent action needed |
| 🔴 **Extremely High** | Critical invasiveness risk — immediate intervention required |

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip or conda package manager
- Modern web browser

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool.git
   cd Fuzzy_Invasive_Species_Risk_Assessment_Tool
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   # Using conda
   conda create -n invasive_species python=3.9
   conda activate invasive_species
   
   # Or using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit numpy
   ```

### Running the Application

```bash
streamlit run invasive_risk_dashboard_app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Home Page
- Review educational information about invasive species
- Understand the assessment process
- Learn about the different models

### Step 2: Model Selection
- Choose between Model I (Equal Weights) or Model II (Expert Weights)
- Compare models side-by-side
- Select the most appropriate for your use case

### Step 3: Input Biological Traits
- **Dispersal Factors:** Enter quantitative measurements
  - Seeds per fruit (numeric input)
  - Annual seed production per m² (numeric input)
  - Seed viability in months (numeric input)
  - Long-distance dispersal potential (slider 0-10)

- **Main Risk Factors:** Select linguistic values
  - Vegetative Reproduction Strength (dropdown)
  - Seed Germination Requirement (dropdown)
  - Human Activity Influence (dropdown)
  - Natural/Man-made Disturbance (dropdown)

### Step 4: View Results
- **Risk Level Display** - Color-coded visual representation
- **Key Metrics** - Summary of calculated values
- **Input Summary** - Review your entered data
- **Management Recommendations** - Evidence-based guidance based on risk level

## 🎮 Navigation

### Main Navigation (Sidebar)
- 🏠 **Home** - Introduction and educational content
- ⚙️ **Model Selection** - Choose assessment model
- 📋 **Input Data** - Enter biological traits
- 💬 **Contact Us** - Get in touch and view FAQ

### Additional Features
- 🌙 **Dark Mode Toggle** - Switch between light and dark themes
- 📚 **Resources** - Quick access to research paper and GitHub
- 🔧 **Settings** - Customize your experience

## 🎨 Themes & Customization

### Dark Mode
Toggle dark mode in the sidebar under Settings. Perfect for:
- Low-light environments
- Reduced eye strain
- Modern aesthetics

### Color Scheme
The application uses a professional bluish color palette:
- **Primary Color:** Sky Blue (#0ea5e9)
- **Secondary Color:** Cyan (#06b6d4)
- **Success Color:** Green (#10b981)
- **Danger Color:** Red (#ef4444)
- **Warning Color:** Amber (#f59e0b)

## 📧 Contact Us & Support

### GitHub Repository
- **Issue Tracker:** Report bugs and request features
- **Discussions:** Ask questions and collaborate
- **Pull Requests:** Contribute improvements

### ResearchGate
- **Paper Access:** View full research publication
- **Author Contact:** Connect with researchers
- **Q&A:** Ask research-related questions

### Contact Form
Use the Contact Us page (💬 button) to:
- Send inquiries
- Report technical issues
- Suggest improvements
- Discuss research collaboration

## 🔗 Important Links

| Link | Purpose |
|---|---|
| [GitHub Repository](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool.git) | Source code, issues, discussions |
| [ResearchGate Paper](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species) | Full research publication |
| `http://localhost:8501` | Dashboard when run locally (`streamlit run invasive_risk_dashboard_app.py`) |

## 📚 Citation

If you use this tool in your research, please cite:

```bibtex
@article{fuzzy_invasive_2017,
  title={Novel Fuzzy Linguistic based Mathematical model to assess risk of Invasive alien plant species},
  journal={Applied Soft Computing},
  year={2017}
}
```

## 🔬 Technical Details

### Backend
- **Language:** Python 3.9+
- **Core Dependencies:**
  - Streamlit 1.50.0 - Web application framework
  - NumPy - Numerical computations
- **Models:** Fuzzy logic operators with linguistic aggregation

### Frontend
- **Framework:** Streamlit
- **Styling:** Custom CSS with CSS variables
- **Design:** Responsive, accessible, modern
- **Themes:** Light and dark mode support

### Architecture
- **Multi-page Application** - 5 pages for different features
- **Session State Management** - Persistent user data
- **Form Validation** - Input verification and error handling
- **Responsive Design** - Mobile-first approach

## 📊 Data Flow

```
User Input (Biological Traits)
       ↓
Membership Function Calculation
       ↓
Fuzzy Aggregation (Model I or II)
       ↓
Linguistic Defuzzification
       ↓
Risk Level Classification
       ↓
Visual Results & Recommendations
```

## ✅ Quality Assurance

- ✓ Peer-reviewed models
- ✓ Validated against field data
- ✓ Comprehensive error handling
- ✓ Intuitive user interface
- ✓ Professional design
- ✓ Accessible to all users
- ✓ Mobile responsive
- ✓ Dark mode support

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is part of academic research. For licensing and usage terms, please contact the authors through the GitHub repository or ResearchGate.

## 🙏 Acknowledgments

- **Research Foundation:** Applied Soft Computing Journal (2017)
- **Fuzzy Logic Framework:** Expert-weighted aggregation operators
- **User Interface:** Streamlit framework
- **Community:** Open-source contributors and researchers

## ❓ FAQ

### How accurate are the assessments?

The models have been validated against real-world field data and show high agreement rates. They serve as a decision-support tool and should be combined with expert judgment and local ecological knowledge.

### Can I use this for commercial purposes?

Please contact us through the GitHub repository or ResearchGate for licensing inquiries and commercial use options.

### Where can I find the original research paper?

Access the full paper at:
- [ResearchGate](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
- [GitHub Repository Documentation](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool)

### How do I report a bug?

Please open an issue on the [GitHub repository](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Screenshots (if applicable)

### Can I contribute to the project?

Yes! We welcome contributions. Please check the GitHub repository for contributing guidelines and open issues.

## 📞 Support

For support and inquiries:
- **GitHub Issues:** [Report bugs and request features](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool/issues)
- **GitHub Discussions:** [Ask questions and discuss ideas](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool/discussions)
- **Contact Form:** Use the 💬 Contact Us page in the application
- **ResearchGate:** [Connect with authors](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Active Development

Made with ❤️ for ecological research and invasive species management.
