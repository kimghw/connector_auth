"""
Graph Filter Helpers - 필터링 헬퍼 함수들
"""

from typing import Optional, List, Dict, Any


class FilterHelpers:
    """필터 헬퍼 클래스"""

    pass


def quick_filter(
    unread: Optional[bool] = None,
    has_attachments: Optional[bool] = None,
    importance: Optional[str] = None,
    from_sender: Optional[str] = None,
    from_any: Optional[List[str]] = None,
    subject: Optional[str] = None,
    subject_any: Optional[List[str]] = None,
    days_back: Optional[int] = None,
    exclude_spam: bool = False,
    exclude_senders: Optional[List[str]] = None,
    exclude_subjects: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Quick filter builder

    Returns:
        Filter parameters dictionary
    """
    params = {}

    if unread is not None:
        params["unread"] = unread
    if has_attachments is not None:
        params["has_attachments"] = has_attachments
    if importance:
        params["importance"] = importance
    if from_sender:
        params["from_sender"] = from_sender
    if from_any:
        params["from_any"] = from_any
    if subject:
        params["subject"] = subject
    if subject_any:
        params["subject_any"] = subject_any
    if days_back:
        params["days_back"] = days_back
    if exclude_spam:
        params["exclude_spam"] = exclude_spam
    if exclude_senders:
        params["exclude_senders"] = exclude_senders
    if exclude_subjects:
        params["exclude_subjects"] = exclude_subjects

    return params
