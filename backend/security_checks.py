"""
セキュリティチェック機能
docsで議論したセキュリティ要件を実装
"""
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
from typing import Union, List, Optional, Dict
import numpy as np


class NoiseType(Enum):
    """ノイズタイプの定義"""
    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"


class DifferentialPrivacy:
    """
    差分プライバシー機構
    統計結果にノイズを付加してプライバシーを保護
    """

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Args:
            epsilon: プライバシーバジェット（小さいほど強いプライバシー保護）
            delta: (ε, δ)-差分プライバシーのδパラメータ（Gaussian用）
        """
        self.epsilon = epsilon
        self.delta = delta

    def calculate_sensitivity(
        self,
        operation: str,
        data_range: tuple,
        sample_size: int
    ) -> float:
        """
        クエリの感度（sensitivity）を計算
        感度 = 1人のデータが変わった時の最大出力変化量

        Args:
            operation: 統計操作（mean, sum, count等）
            data_range: データの範囲 (min, max)
            sample_size: データサイズ

        Returns:
            float: 感度値
        """
        min_val, max_val = data_range
        value_range = max_val - min_val

        if operation == 'mean':
            # 平均の感度 = 範囲 / サンプルサイズ
            return value_range / sample_size

        elif operation == 'sum':
            # 合計の感度 = 1人が追加/削除された時の最大変化
            return value_range

        elif operation == 'count':
            # カウントの感度 = 1
            return 1.0

        elif operation == 'variance' or operation == 'std':
            # 分散の感度（近似）= 範囲^2 / サンプルサイズ
            return (value_range ** 2) / sample_size

        elif operation == 'min' or operation == 'max':
            # 最小/最大の感度 = 範囲（最悪ケース）
            return value_range

        elif operation == 'median':
            # 中央値の感度（近似）
            return value_range / sample_size

        else:
            # 未知の操作の場合は保守的に範囲を返す
            return value_range

    def add_laplace_noise(
        self,
        value: Union[float, List[float], np.ndarray],
        sensitivity: float,
        epsilon: Optional[float] = None
    ) -> Union[float, np.ndarray]:
        """
        Laplace機構によるノイズ付加
        (ε)-差分プライバシーを保証

        Args:
            value: 元の値（スカラーまたは配列）
            sensitivity: クエリの感度
            epsilon: プライバシーパラメータ（Noneの場合はインスタンスの値を使用）

        Returns:
            ノイズ付加後の値
        """
        eps = epsilon if epsilon is not None else self.epsilon

        # Laplaceノイズのスケール = 感度 / ε
        scale = sensitivity / eps

        if isinstance(value, (list, np.ndarray)):
            value_array = np.array(value)
            noise = np.random.laplace(loc=0, scale=scale, size=value_array.shape)
            return value_array + noise
        else:
            noise = np.random.laplace(loc=0, scale=scale)
            return value + noise

    def add_gaussian_noise(
        self,
        value: Union[float, List[float], np.ndarray],
        sensitivity: float,
        epsilon: Optional[float] = None,
        delta: Optional[float] = None
    ) -> Union[float, np.ndarray]:
        """
        Gaussian機構によるノイズ付加
        (ε, δ)-差分プライバシーを保証

        Args:
            value: 元の値（スカラーまたは配列）
            sensitivity: クエリの感度
            epsilon: プライバシーパラメータ
            delta: δパラメータ

        Returns:
            ノイズ付加後の値
        """
        eps = epsilon if epsilon is not None else self.epsilon
        d = delta if delta is not None else self.delta

        # Gaussianノイズの標準偏差
        # σ = sensitivity * sqrt(2 * ln(1.25/δ)) / ε
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / d)) / eps

        if isinstance(value, (list, np.ndarray)):
            value_array = np.array(value)
            noise = np.random.normal(loc=0, scale=sigma, size=value_array.shape)
            return value_array + noise
        else:
            noise = np.random.normal(loc=0, scale=sigma)
            return value + noise

    def add_noise(
        self,
        value: Union[float, List[float], np.ndarray],
        sensitivity: float,
        noise_type: NoiseType = NoiseType.LAPLACE,
        epsilon: Optional[float] = None,
        delta: Optional[float] = None
    ) -> Union[float, np.ndarray]:
        """
        指定されたノイズタイプでノイズを付加

        Args:
            value: 元の値
            sensitivity: クエリの感度
            noise_type: ノイズタイプ（LAPLACE or GAUSSIAN）
            epsilon: プライバシーパラメータ
            delta: δパラメータ（Gaussian用）

        Returns:
            ノイズ付加後の値
        """
        if noise_type == NoiseType.LAPLACE:
            return self.add_laplace_noise(value, sensitivity, epsilon)
        elif noise_type == NoiseType.GAUSSIAN:
            return self.add_gaussian_noise(value, sensitivity, epsilon, delta)
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")

    def apply_to_result(
        self,
        result: Union[float, List[float], np.ndarray],
        operation: str,
        field: str,
        sample_size: int,
        noise_type: NoiseType = NoiseType.LAPLACE
    ) -> Dict:
        """
        統計結果に差分プライバシーを適用

        Args:
            result: 元の統計結果
            operation: 統計操作
            field: フィールド名
            sample_size: サンプルサイズ
            noise_type: ノイズタイプ

        Returns:
            dict: {
                'noisy_result': ノイズ付加後の結果,
                'epsilon_used': 使用したε,
                'noise_type': ノイズタイプ,
                'sensitivity': 感度
            }
        """
        # フィールドごとのデータ範囲（医療データの典型的な範囲）
        field_ranges = {
            'age': (0, 120),
            'blood_pressure_systolic': (80, 200),
            'blood_pressure_diastolic': (50, 130),
            'blood_sugar': (50, 300),
            'cholesterol': (100, 400),
            'bmi': (10, 50),
            'hospitalization_count': (0, 20),
            # デフォルト範囲
            'default': (0, 1000)
        }

        data_range = field_ranges.get(field, field_ranges['default'])

        # 感度を計算
        sensitivity = self.calculate_sensitivity(operation, data_range, sample_size)

        # ノイズを付加
        noisy_result = self.add_noise(
            result,
            sensitivity,
            noise_type,
            self.epsilon,
            self.delta
        )

        return {
            'noisy_result': noisy_result.tolist() if isinstance(noisy_result, np.ndarray)
                           else noisy_result,
            'original_result': result.tolist() if isinstance(result, np.ndarray)
                              else result,
            'epsilon_used': self.epsilon,
            'delta_used': self.delta if noise_type == NoiseType.GAUSSIAN else None,
            'noise_type': noise_type.value,
            'sensitivity': sensitivity,
            'field': field,
            'operation': operation,
            'sample_size': sample_size
        }

    def estimate_noise_magnitude(
        self,
        operation: str,
        field: str,
        sample_size: int,
        noise_type: NoiseType = NoiseType.LAPLACE
    ) -> Dict:
        """
        予想されるノイズの大きさを推定（クエリ前の情報提供用）

        Args:
            operation: 統計操作
            field: フィールド名
            sample_size: サンプルサイズ
            noise_type: ノイズタイプ

        Returns:
            dict: ノイズの推定情報
        """
        field_ranges = {
            'age': (0, 120),
            'blood_pressure_systolic': (80, 200),
            'blood_pressure_diastolic': (50, 130),
            'blood_sugar': (50, 300),
            'cholesterol': (100, 400),
            'bmi': (10, 50),
            'hospitalization_count': (0, 20),
            'default': (0, 1000)
        }

        data_range = field_ranges.get(field, field_ranges['default'])
        sensitivity = self.calculate_sensitivity(operation, data_range, sample_size)

        if noise_type == NoiseType.LAPLACE:
            scale = sensitivity / self.epsilon
            expected_magnitude = scale  # Laplaceの期待絶対値 = scale
            std_dev = np.sqrt(2) * scale
        else:
            sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon
            expected_magnitude = sigma * np.sqrt(2 / np.pi)  # 半正規分布の期待値
            std_dev = sigma

        return {
            'sensitivity': sensitivity,
            'expected_noise_magnitude': expected_magnitude,
            'noise_std_dev': std_dev,
            'noise_type': noise_type.value,
            'epsilon': self.epsilon,
            'recommendation': self._get_recommendation(expected_magnitude, data_range)
        }

    def _get_recommendation(self, noise_magnitude: float, data_range: tuple) -> str:
        """ノイズの大きさに基づく推奨事項を生成"""
        value_range = data_range[1] - data_range[0]
        noise_ratio = noise_magnitude / value_range

        if noise_ratio < 0.01:
            return "優良: ノイズは結果に対して非常に小さく、高精度の統計が得られます"
        elif noise_ratio < 0.05:
            return "良好: ノイズは許容範囲内で、実用的な統計が得られます"
        elif noise_ratio < 0.1:
            return "注意: ノイズがやや大きめです。サンプルサイズを増やすことを推奨します"
        else:
            return "警告: ノイズが大きく、結果の精度が低下する可能性があります"


class SecurityChecker:
    """統合セキュリティチェッカー"""

    def __init__(self):
        self.query_log = []
        self.request_log = defaultdict(list)

    def check_k_anonymity(self, sample_size, min_k=100):
        """
        k-匿名性チェック

        Args:
            sample_size: データのサンプル数
            min_k: 最小k値（デフォルト100）

        Returns:
            bool: k-匿名性を満たす場合True

        Raises:
            ValueError: k-匿名性違反
        """
        if sample_size < min_k:
            raise ValueError(
                f"k-anonymity violation: Need at least {min_k} samples, "
                f"got {sample_size}"
            )
        return True

    def check_aggregate_query(self, query_metadata):
        """
        集約統計クエリかどうかをチェック
        個別データの復号は拒否

        Args:
            query_metadata: クエリのメタデータ

        Returns:
            bool: 集約統計の場合True

        Raises:
            ValueError: 個別データクエリ
        """
        allowed_operations = [
            'mean', 'average', 'sum', 'std', 'variance',
            'median', 'percentile', 'correlation', 'count',
            'min', 'max'
        ]

        operation = query_metadata.get('operation', '')

        if operation not in allowed_operations:
            raise ValueError(
                f"Individual data decryption not allowed. "
                f"Operation '{operation}' is not an aggregate function. "
                f"Allowed: {allowed_operations}"
            )

        return True

    def detect_reconstruction_attack(self, purchaser_id, query_metadata,
                                     similarity_threshold=5, time_window_hours=24):
        """
        データ再構成攻撃を検出
        類似したクエリを繰り返すことで個別データを復元しようとする攻撃を検出

        Args:
            purchaser_id: 購入者ID
            query_metadata: クエリメタデータ
            similarity_threshold: 類似クエリの閾値
            time_window_hours: 監視時間窓（時間）

        Returns:
            bool: 安全な場合True

        Raises:
            ValueError: 攻撃検出時
        """
        # 最近のクエリを取得
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent_queries = [
            q for q in self.query_log
            if q['purchaser_id'] == purchaser_id and q['timestamp'] > cutoff
        ]

        # 類似クエリをカウント
        similar_count = 0
        for past_query in recent_queries:
            if self._queries_similar(past_query['metadata'], query_metadata):
                similar_count += 1

        # 閾値チェック
        if similar_count > similarity_threshold:
            raise ValueError(
                f"Potential data reconstruction attack detected: "
                f"{similar_count} similar queries in last {time_window_hours} hours"
            )

        # クエリをログに記録
        self.query_log.append({
            'purchaser_id': purchaser_id,
            'metadata': query_metadata,
            'timestamp': datetime.now()
        })

        return True

    def _queries_similar(self, query1, query2, threshold=0.8):
        """
        2つのクエリが類似しているかチェック（Jaccard類似度）

        Args:
            query1, query2: 比較するクエリメタデータ
            threshold: 類似度閾値

        Returns:
            bool: 類似している場合True
        """
        # フィルタ条件の集合を作成
        filters1 = set(str(query1.get('filters', {})).split())
        filters2 = set(str(query2.get('filters', {})).split())

        if not filters1 or not filters2:
            return False

        # Jaccard類似度を計算
        intersection = len(filters1 & filters2)
        union = len(filters1 | filters2)

        jaccard_similarity = intersection / union if union > 0 else 0

        return jaccard_similarity > threshold

    def check_rate_limit(self, purchaser_id, max_requests=100, time_window_minutes=60):
        """
        レート制限チェック

        Args:
            purchaser_id: 購入者ID
            max_requests: 最大リクエスト数
            time_window_minutes: 時間窓（分）

        Returns:
            bool: 制限内の場合True

        Raises:
            ValueError: レート制限超過
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=time_window_minutes)

        # 古いリクエストを削除
        self.request_log[purchaser_id] = [
            ts for ts in self.request_log[purchaser_id]
            if ts > cutoff
        ]

        # リクエスト数をチェック
        if len(self.request_log[purchaser_id]) >= max_requests:
            raise ValueError(
                f"Rate limit exceeded: {max_requests} requests per "
                f"{time_window_minutes} minutes"
            )

        # リクエストを記録
        self.request_log[purchaser_id].append(now)

        return True

    def get_remaining_requests(self, purchaser_id, max_requests=100,
                               time_window_minutes=60):
        """
        残りリクエスト数を取得

        Args:
            purchaser_id: 購入者ID
            max_requests: 最大リクエスト数
            time_window_minutes: 時間窓（分）

        Returns:
            int: 残りリクエスト数
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=time_window_minutes)

        recent_requests = [
            ts for ts in self.request_log.get(purchaser_id, [])
            if ts > cutoff
        ]

        return max(0, max_requests - len(recent_requests))

    def validate_metadata(self, metadata):
        """
        メタデータの妥当性をチェック

        Args:
            metadata: クエリメタデータ

        Returns:
            bool: 妥当な場合True

        Raises:
            ValueError: 必須フィールドが欠落
        """
        required_fields = ['operation', 'sample_size']

        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required field: {field}")

        # サンプルサイズが正の整数か
        if not isinstance(metadata['sample_size'], int) or metadata['sample_size'] <= 0:
            raise ValueError("sample_size must be a positive integer")

        return True


class PrivacyBudgetManager:
    """
    プライバシーバジェット管理
    （差分プライバシーは今回不要だが、将来の拡張のため概念を残す）
    """

    def __init__(self, total_budget=10.0):
        """
        Args:
            total_budget: 総プライバシーバジェット
        """
        self.total_budget = total_budget
        self.used_budget = {}

    def check_budget(self, purchaser_id, required_epsilon=0.0):
        """
        バジェットが十分か確認

        Args:
            purchaser_id: 購入者ID
            required_epsilon: 必要なepsilon（今回は0.0）

        Returns:
            bool: バジェットが十分な場合True

        Raises:
            ValueError: バジェット超過
        """
        used = self.used_budget.get(purchaser_id, 0.0)
        remaining = self.total_budget - used

        if required_epsilon > remaining:
            raise ValueError(
                f"Privacy budget exceeded. "
                f"Required: {required_epsilon}, Remaining: {remaining:.2f}"
            )

        return True

    def consume_budget(self, purchaser_id, epsilon=0.0):
        """
        バジェットを消費

        Args:
            purchaser_id: 購入者ID
            epsilon: 消費するepsilon
        """
        if purchaser_id not in self.used_budget:
            self.used_budget[purchaser_id] = 0.0

        self.used_budget[purchaser_id] += epsilon

    def get_remaining_budget(self, purchaser_id):
        """
        残りバジェットを取得

        Args:
            purchaser_id: 購入者ID

        Returns:
            float: 残りバジェット
        """
        used = self.used_budget.get(purchaser_id, 0.0)
        return self.total_budget - used


def log_security_event(event_type, purchaser_id, details, severity='INFO'):
    """
    セキュリティイベントをログに記録

    Args:
        event_type: イベントタイプ
        purchaser_id: 購入者ID
        details: 詳細情報
        severity: 深刻度（INFO/WARNING/ERROR/CRITICAL）
    """
    timestamp = datetime.now().isoformat()

    log_entry = {
        'timestamp': timestamp,
        'event_type': event_type,
        'purchaser_id': purchaser_id,
        'details': details,
        'severity': severity
    }

    # 実際の実装では、ファイルやデータベースに記録
    print(f"[{severity}] {timestamp} - {event_type} - {purchaser_id}: {details}")

    # CRITICALの場合は管理者に通知（実装例）
    if severity == 'CRITICAL':
        # send_alert_to_admin(log_entry)
        pass

    return log_entry
