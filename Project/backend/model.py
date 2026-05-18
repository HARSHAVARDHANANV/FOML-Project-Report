import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import json
from typing import Dict, Tuple

class CustomerSegmentationModel:
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.cluster_stats = None
        self.segment_map = {}
        self.pattern_map = {}
        self.insight_map = {}
        self.optimal_k = 6

        # Thresholds
        self.income_high = None
        self.income_low = None
        self.income_med = None
        self.spending_high = None
        self.spending_low = None
        self.spending_med = None
        self.freq_high = None
        self.freq_low = None
        self.freq_med = None
        self.recency_high = None
        self.recency_low = None
        self.recency_med = None
        self.monetary_high = None
        self.monetary_low = None
        self.monetary_med = None
        self.value_med = None
        self.engagement_med = None
        self.efficiency_med = None

        self.clustering_features = [
            'Income', 'SpendingScore', 'Frequency',
            'Recency', 'Monetary', 'value_score', 'engagement'
        ]

    def fit(self, df: pd.DataFrame) -> None:
        """Train the segmentation model on the dataset"""
        # Feature Engineering
        df = df.copy()
        df['value_score'] = df['Monetary'] * df['Frequency']
        df['engagement'] = df['Frequency'] / (df['Recency'] + 1)
        df['efficiency'] = df['SpendingScore'] / df['Income']
        df['loyalty'] = df['Frequency'] * (1 / df['Recency'])

        # Calculate thresholds
        self.income_high = df['Income'].quantile(0.75)
        self.income_low = df['Income'].quantile(0.25)
        self.income_med = df['Income'].median()
        self.spending_high = df['SpendingScore'].quantile(0.75)
        self.spending_low = df['SpendingScore'].quantile(0.25)
        self.spending_med = df['SpendingScore'].median()
        self.freq_high = df['Frequency'].quantile(0.75)
        self.freq_low = df['Frequency'].quantile(0.25)
        self.freq_med = df['Frequency'].median()
        self.recency_high = df['Recency'].quantile(0.75)
        self.recency_low = df['Recency'].quantile(0.25)
        self.recency_med = df['Recency'].median()
        self.monetary_high = df['Monetary'].quantile(0.75)
        self.monetary_low = df['Monetary'].quantile(0.25)
        self.monetary_med = df['Monetary'].median()
        self.value_med = df['value_score'].median()
        self.engagement_med = df['engagement'].median()
        self.efficiency_med = df['efficiency'].median()

        # Prepare features for clustering
        X = df[self.clustering_features].copy()
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Apply K-Means
        self.kmeans = KMeans(n_clusters=self.optimal_k, random_state=42, n_init=10)
        df['Cluster'] = self.kmeans.fit_predict(X_scaled)

        # Calculate cluster statistics
        self.cluster_stats = df.groupby('Cluster').agg({
            'Income': 'mean',
            'SpendingScore': 'mean',
            'Frequency': 'mean',
            'Recency': 'mean',
            'Monetary': 'mean',
            'value_score': 'mean',
            'engagement': 'mean',
            'efficiency': 'mean',
            'CustomerID': 'count'
        }).round(2)

        # Build segment mappings
        for cluster_id in range(self.optimal_k):
            seg, pat, ins = self._analyze_cluster(cluster_id)
            self.segment_map[cluster_id] = seg
            self.pattern_map[cluster_id] = pat
            self.insight_map[cluster_id] = ins

    def _analyze_cluster(self, cluster_id: int) -> Tuple[str, str, str]:
        """Analyze a cluster and return segment, pattern, and insight"""
        stats = self.cluster_stats.loc[cluster_id]

        income = stats['Income']
        spending = stats['SpendingScore']
        freq = stats['Frequency']
        recency = stats['Recency']
        monetary = stats['Monetary']
        value = stats['value_score']
        engage = stats['engagement']
        efficiency = stats['efficiency']

        is_high_income = income >= self.income_med
        is_low_income = income <= self.income_low
        is_high_spending = spending >= self.spending_med
        is_low_spending = spending <= self.spending_low
        is_high_freq = freq >= self.freq_med
        is_low_freq = freq <= self.freq_low
        is_high_recency = recency >= self.recency_med
        is_low_recency = recency <= self.recency_low
        is_high_value = value >= self.value_med
        is_high_engagement = engage >= self.engagement_med
        is_low_engagement = engage <= self.engagement_med
        is_high_efficiency = efficiency >= self.efficiency_med

        # Determine segment
        if is_high_value and is_high_freq and (not is_high_recency):
            segment = "VIP Customer"
            pattern = "High Value + High Frequency + Active"
            insight = "This is a top-tier customer generating significant revenue. Prioritize retention with exclusive perks, early access to products, and personalized service."
        elif is_high_recency and is_low_freq:
            segment = "Churn Risk Customer"
            pattern = "Inactive + Low Engagement"
            insight = "Customer shows signs of disengagement with long absence and low activity. Launch a win-back campaign with targeted offers and personalized outreach immediately."
        elif is_high_income and is_low_engagement and is_high_recency:
            segment = "Dormant High Potential"
            pattern = "High Income + Low Engagement"
            insight = "High-income customer with untapped potential. Deploy personalized luxury campaigns and VIP experiences to reactivate engagement. The income-engagement gap suggests significant untapped opportunity."
        elif is_high_spending and is_low_freq:
            segment = "Impulsive Buyer"
            pattern = "High Spending Score + Low Frequency"
            insight = "Customer spends when they shop but visits infrequently. Create urgency-driven campaigns and limited-time offers to increase visit frequency."
        elif is_low_income and is_high_freq and is_high_engagement:
            segment = "Loyal Budget Shopper"
            pattern = "Low Income + High Engagement"
            insight = "Highly engaged despite limited budget. Maintain loyalty with value-focused promotions and reward programs to preserve long-term relationship."
        elif is_high_efficiency and is_low_income:
            segment = "Value Maximizer"
            pattern = "High Spending Efficiency + Low Income"
            insight = "Customer optimizes spending efficiency well. Offer smart product recommendations and value-driven promotions to sustain engagement."
        elif is_high_spending and is_high_recency:
            segment = "Declining High Spender"
            pattern = "High Spending + Inactive"
            insight = "Previously valuable customer showing decreased activity. Investigate causes of decline and offer tailored incentives to restore previous spending levels."
        elif (is_high_income == False and is_low_income == False and
              is_high_spending == False and is_low_spending == False):
            segment = "Regular Customer"
            pattern = "Consistent Mid-Level Buyer"
            insight = "Steady contributor with consistent behavior. Focus on gradual upselling and loyalty programs to increase lifetime value over time."
        else:
            if is_high_income:
                if is_high_freq:
                    segment = "Active Affluent Customer"
                    pattern = "High Income + High Frequency"
                    insight = "Affluent customer with strong purchase behavior. Offer premium products and upsell opportunities to maximize value."
                else:
                    segment = "High-Income Low-Frequency"
                    pattern = "High Income + Moderate Engagement"
                    insight = "Customer has spending power but limited engagement. Develop targeted campaigns to increase purchase frequency."
            elif is_high_freq:
                segment = "Frequent Shopper"
                pattern = "High Frequency + Moderate Income"
                insight = "Regular visitor with solid engagement. Focus on increasing basket size through bundle offers and cross-selling."
            else:
                segment = "Standard Customer"
                pattern = self._define_pattern(is_high_income, is_low_income, is_high_spending,
                                              is_low_spending, is_high_freq, is_low_freq,
                                              is_high_recency, is_low_recency)
                insight = "Average engagement across metrics. Implement general retention strategies and monitor for changes in behavior patterns."

        return segment, pattern, insight

    def _define_pattern(self, hi, li, hs, ls, hf, lf, hr, lr):
        traits = []
        if hi:
            traits.append("High Income")
        if li:
            traits.append("Low Income")
        if hs:
            traits.append("High Spending")
        if ls:
            traits.append("Low Spending")
        if hf:
            traits.append("High Frequency")
        if lf:
            traits.append("Low Frequency")
        if hr:
            traits.append("High Recency")
        if lr:
            traits.append("Low Recency")

        if len(traits) >= 2:
            return " + ".join(traits[:3])
        elif len(traits) == 1:
            return traits[0]
        else:
            return "Balanced Profile"

    def predict(self, income: float, spending_score: float, frequency: float,
                recency: float, monetary: float) -> Dict:
        """Predict segment for a single customer"""
        # Calculate derived features
        value_score = monetary * frequency
        engagement = frequency / (recency + 1)

        # Create feature array
        features = np.array([[income, spending_score, frequency, recency,
                             monetary, value_score, engagement]])

        # Scale and predict
        features_scaled = self.scaler.transform(features)
        cluster = int(self.kmeans.predict(features_scaled)[0])

        return {
            "cluster": cluster,
            "segment": self.segment_map[cluster],
            "pattern": self.pattern_map[cluster],
            "insight": self.insight_map[cluster]
        }

    def get_all_customers_with_clusters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get all customers with their cluster assignments for visualization"""
        df = df.copy()
        df['value_score'] = df['Monetary'] * df['Frequency']
        df['engagement'] = df['Frequency'] / (df['Recency'] + 1)

        X = df[self.clustering_features].copy()
        X_scaled = self.scaler.transform(X)
        df['Cluster'] = self.kmeans.predict(X_scaled)

        return df[['CustomerID', 'Income', 'SpendingScore', 'Frequency',
                   'Recency', 'Monetary', 'Cluster']]

# Global model instance
model = CustomerSegmentationModel()

# Initialize model with data
def init_model(data_path: str):
    df = pd.read_csv(data_path)
    model.fit(df)
    return model
