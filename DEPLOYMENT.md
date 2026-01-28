# 🚀 Streamlit Cloud Deployment Guide

This guide will help you deploy the Invasive Species Risk Assessment Dashboard to Streamlit Cloud for free hosting and sharing.

## 📋 Prerequisites

Before you start, make sure you have:

1. ✅ A GitHub account
2. ✅ A Streamlit Cloud account
3. ✅ Git installed on your computer

## 🔧 Step-by-Step Deployment

### Step 1: Prepare Your Repository

Your repository is already set up with:
- ✅ `invasive_risk_dashboard_app.py` - Main application
- ✅ `requirements.txt` - Python dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `README.md` - Documentation

### Step 2: Push Latest Changes to GitHub

Make sure all your changes are pushed to GitHub:

```bash
cd f:\9.project_maths\maths\code
git add -A
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### Step 3: Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit [share.streamlit.io](https://share.streamlit.io/)
   - Sign in with your GitHub account

2. **Create New App:**
   - Click "New app" button
   - Select your GitHub repository: `Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool`
   - Choose the branch: `main`
   - Set the main file path: `invasive_risk_dashboard_app.py`

3. **Deploy:**
   - Click "Deploy!" button
   - Wait for deployment to complete (usually takes 1-2 minutes)

4. **Share Your App:**
   - Copy the deployed URL (it will be something like `https://[your-app-name].streamlit.app`)
   - Share it with others!

## 🌐 Your Deployment URL

Once deployed, your app will be available at:
```
https://<your-app-name>.streamlit.app
```

## ⚙️ Configuration

### Streamlit Config (`config.toml`)

The `.streamlit/config.toml` file is already configured with:

- **Theme:** Bluish color scheme matching the app design
  - Primary Color: Sky Blue (#0ea5e9)
  - Background Color: Light Gray (#f8fafc)
  - Text Color: Dark Blue (#0f172a)

- **UI Settings:**
  - Minimal toolbar for clean interface
  - Sidebar navigation enabled
  - Error details shown for debugging

### Requirements (`requirements.txt`)

The `requirements.txt` includes:
- `streamlit==1.50.0` - Web framework
- `numpy>=1.21.0` - Numerical computations

## 📊 App Features on Streamlit Cloud

Once deployed, your app will have:

- ✅ **5 Pages:**
  1. 🏠 Home - Introduction & educational content
  2. ⚙️ Model Selection - Choose assessment model
  3. 📋 Input Data - Enter biological traits
  4. 📊 Results - View risk assessment
  5. 💬 Contact Us - Get in touch

- ✅ **Dark Mode Toggle** - Switch themes anytime

- ✅ **Professional UI** - Bluish theme with animations

- ✅ **Responsive Design** - Works on desktop, tablet, mobile

- ✅ **Form Handling** - Capture contact inquiries

## 🔗 Useful Links

After deployment, share these with your users:

- **Live App:** `https://[your-app-name].streamlit.app`
- **GitHub Repository:** `https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool`
- **Research Paper:** `https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species`

## 📈 Monitoring Your Deployment

After deployment, you can:

1. **View Logs:**
   - Click on your app in Streamlit Cloud dashboard
   - View recent logs and activity

2. **Check App Health:**
   - Monitor resource usage
   - Check for any errors

3. **Update Your App:**
   - Simply push changes to GitHub `main` branch
   - Streamlit Cloud automatically redeploys

## 🚨 Troubleshooting

### App won't deploy?

1. Check that `requirements.txt` is in the root directory
2. Verify `invasive_risk_dashboard_app.py` is the correct filename
3. Check GitHub repository is public
4. Review deployment logs in Streamlit Cloud dashboard

### Dependencies not installing?

Make sure `requirements.txt` has correct package names:
```
streamlit==1.50.0
numpy>=1.21.0
```

### App runs locally but not on Streamlit Cloud?

- Check for hardcoded file paths (use relative paths instead)
- Ensure all imports are in `requirements.txt`
- Verify your code doesn't use local files

## 💡 Tips for Success

1. **Use Relative Imports:** Always use relative paths for any files
2. **Add Comments:** Document your code for maintenance
3. **Test Locally First:** Run `streamlit run invasive_risk_dashboard_app.py` locally before deploying
4. **Monitor Resource Usage:** Keep an eye on your app's memory and CPU usage
5. **Get Feedback:** Share the link and gather user feedback for improvements

## 🔄 Continuous Deployment

Every time you push to the `main` branch on GitHub:
1. Streamlit Cloud automatically detects the changes
2. Your app automatically redeploys
3. Users always see the latest version

## 📞 Need Help?

- **Streamlit Cloud Docs:** [docs.streamlit.io/streamlit-cloud](https://docs.streamlit.io/streamlit-cloud)
- **Streamlit Community:** [discuss.streamlit.io](https://discuss.streamlit.io)
- **Contact Form:** Use the 💬 Contact Us page in your deployed app

## ✅ Deployment Checklist

Before deploying, verify:

- ✅ `requirements.txt` exists with all dependencies
- ✅ `.streamlit/config.toml` is configured
- ✅ `invasive_risk_dashboard_app.py` is the main file
- ✅ All changes are pushed to GitHub
- ✅ GitHub repository is public
- ✅ App runs locally without errors

## 🎉 Congratulations!

Your Invasive Species Risk Assessment Dashboard is ready to deploy and share with the world!

---

**Questions?** Check the FAQ in the Contact Us page or open an issue on GitHub!
