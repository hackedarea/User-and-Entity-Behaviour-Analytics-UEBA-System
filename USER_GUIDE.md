# 🛡️ UEBA System v3.1 - User Guide

> **Complete User Manual for Enterprise Cybersecurity Platform**  
> Version: 3.1 | Date: October 6, 2025 | Status: Production Ready

---

## 🎯 **QUICK START GUIDE**

### **System Launch**
```bash
python ueba_launcher.py
```

### **Access Points**
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Elasticsearch API**: http://localhost:9200
- **System Status**: EXCELLENT ✨

---

## 📋 **COMPLETE MENU OPTIONS GUIDE**

### 🚀 **QUICK ACTIONS**

#### **1. 🔧 Quick Deploy (Start everything)**
**Purpose**: Complete system initialization and deployment  
**Duration**: ~11.6 seconds  
**What it does**:
- ✅ Starts Docker services (Elasticsearch + Grafana)
- ✅ Generates 200 realistic security events
- ✅ Runs optimized ML analysis
- ✅ Provides access URLs

**Best for**: First-time setup and system initialization

---

#### **2. 🔍 System Health Check**
**Purpose**: Comprehensive system diagnostic  
**Duration**: ~10 seconds  
**What it checks**:
- ✅ Python environment (3.13.5)
- ✅ All required packages
- ✅ Docker containers status
- ✅ Service connections
- ✅ File structure integrity
- ✅ ML models availability

**Best for**: Regular system monitoring and troubleshooting

---

#### **3. ⚡ Fast Security Analysis**
**Purpose**: Quick threat detection analysis  
**Duration**: ~1.67 seconds  
**Performance**: 
- **Dataset**: 300 events (15% attacks)
- **Features**: 11 engineered features
- **Accuracy**: 98.3-100% (RandomForest/IsolationForest)

**Best for**: Quick security assessment

---

### 📊 **ANALYSIS OPTIONS**

#### **4. 🧠 Interactive ML Analysis**
**Purpose**: Interactive analysis with multiple options  
**Sub-options**:
1. **Quick System Check**: Health verification
2. **Fast Analysis**: 500 events (~0.66s)
3. **Comprehensive Analysis**: 1000 events (~0.48s) 
4. **Speed Test**: 100 events (~0.39s)
5. **Custom Analysis**: User-defined dataset size
6. **View Recent Results**: Historical analysis review

**Best for**: Detailed investigation and performance testing

---

#### **5. 🤖 AutoML Optimization**
**Purpose**: Advanced hyperparameter optimization  
**Duration**: ~1-2 minutes  
**Algorithms**:
- **RandomForest**: F1=0.820, Accuracy=0.924
- **XGBoost**: F1=0.793, Accuracy=0.932
- **LightGBM**: F1=0.811, Accuracy=0.936
- **SVM**: F1=0.845, Accuracy=0.944
- **Ensemble**: F1=1.000, Accuracy=1.000

**Best for**: Model optimization and performance tuning

---

#### **6. 🧬 Neural Network Training**
**Purpose**: Deep learning model training  
**Duration**: ~2-3 minutes  
**Models**:
- **LSTM**: 85.7% accuracy (sequential patterns)
- **CNN**: 53.1% accuracy (feature patterns)
- **Hybrid**: 67.3% accuracy (combined approach)
- **Ensemble**: 85.7% accuracy (best performance)

**Best for**: Advanced threat pattern recognition

---

#### **7. 🛡️ Advanced ML Detection**
**Purpose**: Comprehensive anomaly detection  
**Duration**: ~30-60 seconds  
**Algorithms**:
- **Isolation Forest**: 10.0% anomalies detected
- **One-Class SVM**: 10.3% anomalies detected
- **Local Outlier Factor**: 9.3% anomalies detected
- **DBSCAN Clustering**: 10.0% anomalies detected
- **Ensemble**: 8.7% combined anomalies

**Best for**: Detailed security analysis and threat hunting

---

### 🛠️ **ADVANCED OPTIONS**

#### **8. 📈 Generate Sample Data**
**Purpose**: Create realistic security events for testing  
**Features**:
- Configurable event count
- Realistic attack patterns (15% attack rate)
- Immediate Elasticsearch indexing
- Attack/normal event distribution

**Best for**: Testing, training, and demonstration

---

#### **9. 🚨 ML Alerting System**
**Purpose**: Real-time threat alerting and monitoring  
**Duration**: Configurable (default 30 minutes)  
**Features**:
- Risk level classification (CRITICAL/HIGH/MEDIUM/LOW)
- Threshold-based alerting
- Continuous monitoring
- Alert logging

**Best for**: Production monitoring and incident response

---

#### **10. 📊 View Results**
**Purpose**: Historical analysis review and reporting  
**Features**:
- Recent analysis results
- Performance metrics
- Trend analysis
- Export capabilities

**Best for**: Reporting and analysis review

---

#### **11. 📡 Real-time ML Monitoring**
**Purpose**: Live threat detection and monitoring  
**Duration**: Configurable (default 60 minutes)  
**Features**:
- **Live Processing**: 3 ML models (Isolation Forest, One-Class SVM, LOF)
- **Real-time Stats**: Events processed, anomalies detected, processing rates
- **Performance Metrics**: Average prediction time, anomaly rates
- **Elasticsearch Integration**: Version-compatible HTTP API

**Best for**: Continuous security monitoring and live threat detection

---

## 🎯 **PERFORMANCE BENCHMARKS**

### **Speed Performance**
- **Quick Deploy**: 11.6 seconds (full system)
- **Fast Analysis**: 1.67 seconds (300 events)
- **Speed Test**: 0.39 seconds (100 events)
- **AutoML Training**: 60 seconds (4 algorithms)

### **Accuracy Performance**
- **AutoML Ensemble**: 100% accuracy, F1=1.000
- **Neural Networks**: Up to 85.7% accuracy
- **Anomaly Detection**: 98-100% precision
- **Real-time Processing**: <50ms per event

---

## 🔧 **TECHNICAL SPECIFICATIONS**

### **System Requirements**
- **Python**: 3.13.5+
- **Docker**: Latest version
- **Memory**: 8GB+ recommended
- **Storage**: 2GB+ for models and data

### **External Dependencies**
- **Elasticsearch**: 8.10.2 (auto-configured)
- **Grafana**: 10.2.0 (auto-configured)
- **ML Libraries**: TensorFlow, scikit-learn, XGBoost, LightGBM

### **Data Processing**
- **Input**: Elasticsearch logs, custom datasets
- **Features**: 11-30 engineered features per algorithm
- **Output**: JSON reports, trained models, alerts

---

## 🛡️ **SECURITY FEATURES**

### **Threat Detection**
- **Attack Types**: SQL injection, XSS, directory traversal, RFI, LFI
- **Detection Methods**: Anomaly detection, pattern recognition, ML classification
- **Response Time**: Real-time to sub-second processing

### **Analysis Capabilities**
- **Behavioral Analysis**: User pattern deviation detection
- **Temporal Analysis**: Time-based anomaly identification
- **Ensemble Detection**: Multiple algorithm consensus

---

## 📊 **TROUBLESHOOTING**

### **Common Issues**

#### **Docker Services Not Running**
```bash
# Check status
docker ps

# Restart if needed
python ueba_launcher.py
# Select option 1 (Quick Deploy)
```

#### **Elasticsearch Connection Issues**
- Verify Docker containers are running
- Check http://localhost:9200 accessibility
- Use option 2 (System Health Check) for diagnosis

#### **Performance Issues**
- Ensure sufficient memory (8GB+)
- Check Docker resource allocation
- Use smaller datasets for testing

### **Support Commands**
```bash
# Full system check
python analytics-engine/system_health_checker.py

# System audit
python analytics-engine/system_audit.py

# Manual Elasticsearch test
curl http://localhost:9200
```

---

## 🎉 **GETTING STARTED CHECKLIST**

### **First Time Setup**
1. ✅ Run `python ueba_launcher.py`
2. ✅ Select option 1 (Quick Deploy)
3. ✅ Verify all services started successfully
4. ✅ Access Grafana at http://localhost:3000
5. ✅ Run option 2 (System Health Check)

### **Daily Operations**
1. ✅ Option 2: System Health Check
2. ✅ Option 3: Fast Security Analysis
3. ✅ Option 11: Real-time ML Monitoring (as needed)
4. ✅ Option 10: View Results (for reporting)

### **Weekly Maintenance**
1. ✅ Option 5: AutoML Optimization (model tuning)
2. ✅ Option 7: Advanced ML Detection (comprehensive analysis)
3. ✅ Review Grafana dashboards for trends

---

## 📞 **SUPPORT & DOCUMENTATION**

### **Additional Resources**
- **System Memory**: `PROJECT_MEMORY.md`
- **Technical Details**: `SYSTEM_VERIFICATION_COMPLETE.md`
- **Docker Setup**: `DOCKER_INSTALLATION_GUIDE.md`

### **Performance Monitoring**
- **Grafana**: Real-time dashboards
- **Elasticsearch**: Data storage and retrieval
- **System Logs**: Detailed execution logs

---

**🛡️ UEBA System v3.1 - Enterprise Cybersecurity Platform**  
*Production Ready | Optimized | Clean | Fast | User-Friendly*

---
*Last Updated: October 6, 2025*
*Version: 3.1 - Production Ready*