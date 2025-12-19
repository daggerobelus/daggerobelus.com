#!/usr/bin/env python3
"""
Module 07: Logistic Regression Analysis for Lorraine Witchcraft Trials
Predicts accusation based on network position and attributes.

Research Questions:
- What network positions predicted becoming accused?
- Did high centrality indicate power or vulnerability?
- How did gender and kinship affect accusation risk?
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve
)
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline")
NETWORK_DIR = BASE_DIR / "output/networks"
ENTITY_DIR = BASE_DIR / "output/entities"
METRICS_DIR = BASE_DIR / "output/metrics"
ROLES_DIR = BASE_DIR / "output/roles"
OUTPUT_DIR = BASE_DIR / "output/models"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class AccusationPredictor:
    """
    Logistic regression model predicting accusation from network features.
    """

    def __init__(self):
        self.G = None
        self.centrality_df = None
        self.canonical_entities = None
        self.model_data = None
        self.model = None
        self.scaler = None

    def load_data(self):
        """Load network and entity data."""
        print("Loading data...")

        # Load network
        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Network: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

        # Load centrality metrics
        self.centrality_df = pd.read_csv(METRICS_DIR / "centrality_all_nodes.csv", index_col=0)
        print(f"  Centrality metrics: {len(self.centrality_df)} nodes")

        # Load canonical entities
        with open(ENTITY_DIR / "canonical_entities.json") as f:
            self.canonical_entities = json.load(f)
        print(f"  Canonical entities: {len(self.canonical_entities)}")

        # Load brokerage scores
        self.brokerage_df = pd.read_csv(ROLES_DIR / "brokerage_scores.csv")
        print(f"  Brokerage scores: {len(self.brokerage_df)} nodes")

    def prepare_model_data(self) -> pd.DataFrame:
        """Prepare features and target for logistic regression using graph nodes directly.

        Accused status is inferred from being a TARGET of TESTIFIED_AGAINST edges.
        Witness status is inferred from being a SOURCE of TESTIFIED_AGAINST edges.
        """
        print("\n=== Preparing Model Data ===")

        # Infer accused/witness status from edge types
        accused_set = set()
        witness_set = set()
        for u, v, data in self.G.edges(data=True):
            if data.get('relationship_type') == 'TESTIFIED_AGAINST':
                accused_set.add(v)  # target is accused
                witness_set.add(u)  # source is witness

        print(f"  Inferred {len(accused_set)} accused (targets of TESTIFIED_AGAINST)")
        print(f"  Inferred {len(witness_set)} witnesses (sources of TESTIFIED_AGAINST)")

        # Use centrality dataframe as base - it has all nodes from the network
        df = self.centrality_df.copy()
        df['node_name'] = df.index
        df = df.reset_index(drop=True)

        # Create brokerage lookup
        brokerage_lookup = dict(zip(self.brokerage_df['node'], self.brokerage_df['brokerage_score']))

        records = []

        for _, row in df.iterrows():
            node_name = row['node_name']
            node_attrs = self.G.nodes.get(node_name, {})

            # Use inferred status based on edge types
            is_accused = int(node_name in accused_set)
            is_witness = int(node_name in witness_set)

            gender = node_attrs.get('gender', 'unknown')

            record = {
                'node_name': node_name,
                'is_accused': is_accused,
                'is_witness': is_witness,
                'gender': gender,
                'gender_female': int(gender == 'female'),
                'gender_male': int(gender == 'male'),
                'brokerage_score': brokerage_lookup.get(node_name, 0),
            }

            # Add centrality metrics
            for col in ['degree', 'betweenness_centrality', 'pagerank',
                       'closeness_centrality', 'eigenvector_centrality',
                       'clustering_coefficient', 'constraint']:
                if col in row:
                    record[col] = row[col] if pd.notna(row[col]) else 0
                else:
                    record[col] = 0

            records.append(record)

        df = pd.DataFrame(records)
        df = df.fillna(0)

        print(f"  Total records: {len(df)}")
        print(f"  Accused (edge-inferred): {df['is_accused'].sum()} ({100*df['is_accused'].mean():.1f}%)")
        print(f"  Witnesses (edge-inferred): {df['is_witness'].sum()} ({100*df['is_witness'].mean():.1f}%)")
        print(f"  Gender distribution: male={df['gender_male'].sum()}, female={df['gender_female'].sum()}")

        self.model_data = df
        return df

    def fit_accusation_model(self) -> Dict:
        """Fit logistic regression to predict accusation."""
        print("\n=== Fitting Accusation Prediction Model ===")

        # Feature columns (exclude has_kinship_ties and num_trial_appearances - not available)
        feature_cols = [
            'degree', 'betweenness_centrality', 'pagerank',
            'closeness_centrality', 'eigenvector_centrality',
            'clustering_coefficient', 'brokerage_score',
            'gender_female', 'gender_male'
        ]

        # Prepare data
        df = self.model_data.copy()

        # Filter to nodes with some network presence (degree > 0)
        df_model = df[df['degree'] > 0].copy()

        print(f"  Modeling {len(df_model)} nodes with degree > 0")
        print(f"  Accused in model set: {df_model['is_accused'].sum()}")

        X = df_model[feature_cols].values
        y = df_model['is_accused'].values

        # Standardize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Fit model
        self.model = LogisticRegression(
            penalty='l2',
            C=1.0,
            class_weight='balanced',  # Handle class imbalance
            max_iter=1000,
            random_state=42
        )
        self.model.fit(X_scaled, y)

        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='roc_auc')

        print(f"\n  Cross-validation AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")

        # Predictions for full analysis
        y_pred = self.model.predict(X_scaled)
        y_prob = self.model.predict_proba(X_scaled)[:, 1]

        # Metrics
        print("\n  Classification Report:")
        print(classification_report(y, y_pred, target_names=['Not Accused', 'Accused']))

        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        print(f"\n  Confusion Matrix:")
        print(f"    TN={cm[0,0]}, FP={cm[0,1]}")
        print(f"    FN={cm[1,0]}, TP={cm[1,1]}")

        # ROC AUC
        roc_auc = roc_auc_score(y, y_prob)
        print(f"\n  ROC AUC: {roc_auc:.3f}")

        # Feature importance (coefficients)
        print("\n  Feature Coefficients (Odds Ratios):")
        coef_df = pd.DataFrame({
            'feature': feature_cols,
            'coefficient': self.model.coef_[0],
            'odds_ratio': np.exp(self.model.coef_[0])
        }).sort_values('coefficient', ascending=False)

        for _, row in coef_df.iterrows():
            direction = "+" if row['coefficient'] > 0 else ""
            print(f"    {row['feature']:30s}: {direction}{row['coefficient']:.4f} (OR={row['odds_ratio']:.3f})")

        # Store results
        results = {
            'cv_auc_mean': cv_scores.mean(),
            'cv_auc_std': cv_scores.std(),
            'roc_auc': roc_auc,
            'n_samples': len(y),
            'n_accused': int(y.sum()),
            'coefficients': dict(zip(feature_cols, self.model.coef_[0].tolist())),
            'odds_ratios': dict(zip(feature_cols, np.exp(self.model.coef_[0]).tolist())),
            'intercept': float(self.model.intercept_[0]),
        }

        # Add predictions to model_data
        df_model['predicted_prob'] = y_prob
        df_model['predicted_accused'] = y_pred
        self.model_data = df_model

        return results, coef_df

    def analyze_misclassifications(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze false positives and false negatives."""
        print("\n=== Misclassification Analysis ===")

        df = self.model_data

        # False positives: predicted accused but not actually accused
        false_positives = df[(df['predicted_accused'] == 1) & (df['is_accused'] == 0)]
        false_positives = false_positives.sort_values('predicted_prob', ascending=False)

        print(f"\n  False Positives: {len(false_positives)} (predicted accused, actually not)")
        print("  Top 10 false positives (high-risk non-accused):")
        for _, row in false_positives.head(10).iterrows():
            print(f"    {row['node_name'][:40]}: prob={row['predicted_prob']:.3f}, "
                  f"degree={row['degree']:.0f}")

        # False negatives: not predicted but actually accused
        false_negatives = df[(df['predicted_accused'] == 0) & (df['is_accused'] == 1)]
        false_negatives = false_negatives.sort_values('predicted_prob', ascending=False)

        print(f"\n  False Negatives: {len(false_negatives)} (not predicted, actually accused)")
        print("  Top 10 false negatives (low-risk accused):")
        for _, row in false_negatives.head(10).iterrows():
            print(f"    {row['node_name'][:40]}: prob={row['predicted_prob']:.3f}, "
                  f"degree={row['degree']:.0f}")

        return false_positives, false_negatives

    def fit_witness_to_accused_model(self) -> Dict:
        """Fit model comparing witnesses who became accused vs those who didn't.

        Note: This requires cross-referencing with canonical entities data.
        Since we're using graph-based approach, we'll skip this supplementary model.
        """
        print("\n=== Witness-to-Accused Transition Model ===")
        print("  Note: This model requires entity-level tracking across trials.")
        print("  See role analysis output for witness-to-accused transitions.")
        print("  Skipping supplementary model - primary accusation model is sufficient.")

        # Return empty results - the role analysis already captured transitions
        results = {
            'note': 'See roles/witness_to_accused_transitions.csv for transition analysis',
            'n_transitions_identified': 9,  # From role analysis
        }

        return results

    def _fit_witness_to_accused_model_DISABLED(self) -> Dict:
        """[DISABLED] Original model - kept for reference."""
        print("\n=== Witness-to-Accused Transition Model ===")

        # Filter to witnesses only
        df_witnesses = self.model_data[self.model_data['is_witness'] == 1].copy()

        if len(df_witnesses) < 50:
            print("  Insufficient data for witness-to-accused model")
            return {}

        feature_cols = [
            'degree', 'betweenness_centrality', 'pagerank',
            'closeness_centrality', 'brokerage_score',
            'gender_female'
        ]

        X = df_witnesses[feature_cols].values
        # Would need witness_to_accused target which requires entity linking
        y = np.zeros(len(df_witnesses))  # placeholder

        print(f"  Modeling {len(df_witnesses)} witnesses")
        print(f"  Became accused: {y.sum()}")

        if y.sum() < 3:
            print("  Too few transitions for reliable model")
            return {}

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Fit model
        model = LogisticRegression(
            penalty='l2',
            C=0.1,  # More regularization for small sample
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        )
        model.fit(X_scaled, y)

        # Print coefficients
        print("\n  Feature Coefficients (Odds Ratios):")
        for feat, coef in zip(feature_cols, model.coef_[0]):
            direction = "+" if coef > 0 else ""
            print(f"    {feat:30s}: {direction}{coef:.4f} (OR={np.exp(coef):.3f})")

        results = {
            'n_witnesses': len(y),
            'n_transitions': int(y.sum()),
            'coefficients': dict(zip(feature_cols, model.coef_[0].tolist())),
            'odds_ratios': dict(zip(feature_cols, np.exp(model.coef_[0]).tolist())),
        }

        return results

    def save_outputs(self, accusation_results: Dict, coef_df: pd.DataFrame,
                    witness_results: Dict):
        """Save all model outputs."""
        print("\n=== Saving Outputs ===")

        # Save model data with predictions
        self.model_data.to_csv(OUTPUT_DIR / "accusation_model_data.csv", index=False)
        print(f"  Saved accusation_model_data.csv ({len(self.model_data)} rows)")

        # Save coefficients
        coef_df.to_csv(OUTPUT_DIR / "accusation_coefficients.csv", index=False)
        print(f"  Saved accusation_coefficients.csv")

        # Save combined results
        all_results = {
            'accusation_model': accusation_results,
            'witness_transition_model': witness_results,
        }

        with open(OUTPUT_DIR / "logistic_regression_results.json", 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"  Saved logistic_regression_results.json")

        # Generate interpretation summary
        summary = self._generate_interpretation(accusation_results, witness_results)
        with open(OUTPUT_DIR / "model_interpretation.txt", 'w') as f:
            f.write(summary)
        print(f"  Saved model_interpretation.txt")

    def _generate_interpretation(self, acc_results: Dict, wit_results: Dict) -> str:
        """Generate human-readable interpretation of results."""
        lines = [
            "=" * 70,
            "LOGISTIC REGRESSION MODEL INTERPRETATION",
            "Lorraine Witchcraft Trials - Accusation Prediction",
            "=" * 70,
            "",
            "1. ACCUSATION MODEL SUMMARY",
            "-" * 40,
            f"Sample Size: {acc_results.get('n_samples', 0)} individuals",
            f"Accused: {acc_results.get('n_accused', 0)} ({100*acc_results.get('n_accused', 0)/max(acc_results.get('n_samples', 1), 1):.1f}%)",
            f"Cross-validated AUC: {acc_results.get('cv_auc_mean', 0):.3f} (+/- {acc_results.get('cv_auc_std', 0)*2:.3f})",
            "",
            "2. KEY PREDICTORS OF ACCUSATION",
            "-" * 40,
        ]

        # Sort by odds ratio
        odds = acc_results.get('odds_ratios', {})
        sorted_odds = sorted(odds.items(), key=lambda x: abs(x[1] - 1), reverse=True)

        for feat, or_val in sorted_odds[:5]:
            if or_val > 1:
                interpretation = f"increases accusation risk by {(or_val-1)*100:.0f}%"
            else:
                interpretation = f"decreases accusation risk by {(1-or_val)*100:.0f}%"
            lines.append(f"  - {feat}: OR={or_val:.3f} ({interpretation})")

        lines.extend([
            "",
            "3. INTERPRETATION",
            "-" * 40,
        ])

        # Interpret key findings
        if 'gender_female' in odds:
            if odds['gender_female'] > 1.5:
                lines.append("  * Being female substantially increases accusation risk")
            elif odds['gender_female'] < 0.67:
                lines.append("  * Being female decreases accusation risk")
            else:
                lines.append("  * Gender has modest effect on accusation risk")

        if 'betweenness_centrality' in odds:
            if odds['betweenness_centrality'] > 1.2:
                lines.append("  * Central network positions (brokers) face higher risk")
            elif odds['betweenness_centrality'] < 0.8:
                lines.append("  * Central network positions appear protective")

        if 'degree' in odds:
            if odds['degree'] > 1.2:
                lines.append("  * More connections correlate with higher accusation risk")
            elif odds['degree'] < 0.8:
                lines.append("  * More connections appear somewhat protective")

        lines.extend([
            "",
            "4. CAVEATS",
            "-" * 40,
            "  * Network position may reflect accusation rather than predict it",
            "  * Historical data has inherent selection biases",
            "  * Model assumes linear effects in log-odds",
            "",
            "=" * 70,
        ])

        return "\n".join(lines)

    def run(self):
        """Execute the full logistic regression pipeline."""
        print("=" * 70)
        print("LOGISTIC REGRESSION ANALYSIS PIPELINE")
        print("=" * 70)

        # Load data
        self.load_data()

        # Prepare features
        self.prepare_model_data()

        # Fit accusation model
        acc_results, coef_df = self.fit_accusation_model()

        # Analyze misclassifications
        self.analyze_misclassifications()

        # Fit witness-to-accused model
        wit_results = self.fit_witness_to_accused_model()

        # Save outputs
        self.save_outputs(acc_results, coef_df, wit_results)

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return acc_results, wit_results


if __name__ == "__main__":
    predictor = AccusationPredictor()
    results = predictor.run()
