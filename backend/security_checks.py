"""
セキュリティチェック機能
docsで議論したセキュリティ要件を実装
"""
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np


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
