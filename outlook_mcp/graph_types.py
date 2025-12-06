"""
Microsoft Graph API 메일 필터링을 위한 타입 정의
"""
from typing import TypedDict, Literal, Optional, List, Union
from datetime import datetime


class FilterParams(TypedDict, total=False):
    """메일 필터링 파라미터 (포함 조건)"""

    # 발신자 관련
    from_address: Optional[Union[str, List[str]]]  # from/emailAddress/address - 단일 또는 여러 발신자
    sender_address: Optional[Union[str, List[str]]]  # sender/emailAddress/address - 단일 또는 여러 발신자

    # 날짜/시간 관련
    # 단일 날짜 필터 (ge 연산자만 사용)
    received_date_time: Optional[str]  # ISO 8601 형식 (예: 2024-12-01T00:00:00Z) - ge 연산자 사용
    sent_date_time: Optional[str]  # ge 연산자 사용
    created_date_time: Optional[str]  # ge 연산자 사용
    last_modified_date_time: Optional[str]  # ge 연산자 사용

    # 날짜 범위 필터 (received_date_time의 확장 버전)
    received_date_from: Optional[str]  # receivedDateTime ge (시작일 이상)
    received_date_to: Optional[str]    # receivedDateTime le (종료일 이하)
    sent_date_from: Optional[str]      # sentDateTime ge (시작일 이상)
    sent_date_to: Optional[str]        # sentDateTime le (종료일 이하)

    # 메시지 상태
    is_read: Optional[bool]
    is_draft: Optional[bool]
    has_attachments: Optional[bool]
    is_delivery_receipt_requested: Optional[bool]
    is_read_receipt_requested: Optional[bool]

    # 메시지 속성
    importance: Optional[Literal["low", "normal", "high"]]
    sensitivity: Optional[Literal["normal", "personal", "private", "confidential"]]
    inference_classification: Optional[Literal["focused", "other"]]

    # 내용 관련 - 단일 키워드 또는 리스트 (리스트는 OR로 연결)
    subject: Optional[Union[str, List[str]]]  # 제목 키워드
    body_content: Optional[Union[str, List[str]]]  # body/content 키워드
    body_preview: Optional[Union[str, List[str]]]  # 미리보기 키워드

    # 키워드 연결 방식 (리스트일 때만 적용)
    subject_operator: Optional[Literal["or", "and"]]  # 기본값: "or"
    body_operator: Optional[Literal["or", "and"]]  # 기본값: "or"

    # ID 관련
    id: Optional[str]  # 메일 고유 ID
    conversation_id: Optional[str]  # 대화 스레드 ID
    parent_folder_id: Optional[str]  # 폴더 ID

    # 카테고리 및 플래그
    categories: Optional[List[str]]  # 카테고리 목록
    flag_status: Optional[Literal["notFlagged", "complete", "flagged"]]  # flag/flagStatus


class ExcludeParams(TypedDict, total=False):
    """메일 제외 파라미터 (제외 조건)"""

    # 발신자 제외 - 단일 문자열 또는 리스트 지원
    exclude_from_address: Optional[Union[str, List[str]]]
    exclude_sender_address: Optional[Union[str, List[str]]]

    # 키워드 제외
    exclude_subject_keywords: Optional[List[str]]  # 제목에서 제외할 키워드들
    exclude_body_keywords: Optional[List[str]]  # 본문에서 제외할 키워드들
    exclude_preview_keywords: Optional[List[str]]  # 미리보기에서 제외할 키워드들

    # 속성 제외
    exclude_importance: Optional[Literal["low", "normal", "high"]]
    exclude_sensitivity: Optional[Literal["normal", "personal", "private", "confidential"]]
    exclude_classification: Optional[Literal["focused", "other"]]

    # 상태 제외
    exclude_read_status: Optional[bool]
    exclude_draft_status: Optional[bool]
    exclude_attachment_status: Optional[bool]
    exclude_delivery_receipt: Optional[bool]
    exclude_read_receipt: Optional[bool]

    # 플래그 및 카테고리 제외
    exclude_flag_status: Optional[Literal["notFlagged", "complete", "flagged"]]
    exclude_categories: Optional[List[str]]

    # ID 제외
    exclude_id: Optional[str]
    exclude_conversation_id: Optional[str]
    exclude_parent_folder_id: Optional[str]


class SelectParams(TypedDict, total=False):
    """메일 조회 시 선택할 필드"""

    fields: List[Literal[
        # 기본 정보
        "id",
        "createdDateTime",
        "lastModifiedDateTime",
        "changeKey",

        # 카테고리
        "categories",

        # 날짜/시간
        "receivedDateTime",
        "sentDateTime",

        # 메일 속성
        "hasAttachments",
        "internetMessageId",
        "subject",
        "bodyPreview",
        "importance",
        "parentFolderId",
        "conversationId",
        "conversationIndex",

        # 상태
        "isDeliveryReceiptRequested",
        "isReadReceiptRequested",
        "isRead",
        "isDraft",

        # 링크 및 분류
        "webLink",
        "inferenceClassification",

        # 복합 객체
        "body",
        "sender",
        "from",
        "toRecipients",
        "ccRecipients",
        "bccRecipients",
        "replyTo",
        "flag"
    ]]


class MailQueryParams(TypedDict, total=False):
    """전체 메일 쿼리 파라미터"""

    filter: Optional[FilterParams]
    exclude: Optional[ExcludeParams]
    select: Optional[SelectParams]

    # 추가 쿼리 옵션
    top: Optional[int]  # 최대 1000
    skip: Optional[int]  # 페이징용
    orderby: Optional[str]  # 정렬 기준
    search: Optional[str]  # $search 파라미터 (filter와 동시 사용 불가)
    count: Optional[bool]  # 총 개수 포함 여부


# 헬퍼 함수들 - 파라미터 생성
def create_filter_params(
    # 발신자 - 단일 문자열 또는 리스트 지원
    from_address: Optional[Union[str, List[str]]] = None,
    sender_address: Optional[Union[str, List[str]]] = None,
    # 날짜/시간 - 단일 날짜 (ge 연산자)
    received_date_time: Optional[str] = None,
    sent_date_time: Optional[str] = None,
    created_date_time: Optional[str] = None,
    last_modified_date_time: Optional[str] = None,
    # 날짜 범위 필터
    received_date_from: Optional[str] = None,
    received_date_to: Optional[str] = None,
    sent_date_from: Optional[str] = None,
    sent_date_to: Optional[str] = None,
    # 상태
    is_read: Optional[bool] = None,
    is_draft: Optional[bool] = None,
    has_attachments: Optional[bool] = None,
    # 속성
    importance: Optional[Literal["low", "normal", "high"]] = None,
    sensitivity: Optional[Literal["normal", "personal", "private", "confidential"]] = None,
    inference_classification: Optional[Literal["focused", "other"]] = None,
    # 내용 - 단일 키워드 또는 리스트
    subject: Optional[Union[str, List[str]]] = None,
    body_content: Optional[Union[str, List[str]]] = None,
    body_preview: Optional[Union[str, List[str]]] = None,
    # 키워드 연결 방식 (리스트일 때만 적용)
    subject_operator: Optional[Literal["or", "and"]] = None,
    body_operator: Optional[Literal["or", "and"]] = None,
    # ID
    id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    parent_folder_id: Optional[str] = None,
    # 카테고리/플래그
    categories: Optional[List[str]] = None,
    flag_status: Optional[Literal["notFlagged", "complete", "flagged"]] = None
) -> FilterParams:
    """FilterParams 객체를 생성하는 헬퍼 함수"""
    params: FilterParams = {}

    # 값이 None이 아닌 것만 추가
    if from_address is not None:
        params['from_address'] = from_address
    if sender_address is not None:
        params['sender_address'] = sender_address
    if received_date_time is not None:
        params['received_date_time'] = received_date_time
    if sent_date_time is not None:
        params['sent_date_time'] = sent_date_time
    if created_date_time is not None:
        params['created_date_time'] = created_date_time
    if last_modified_date_time is not None:
        params['last_modified_date_time'] = last_modified_date_time
    # 날짜 범위 필드
    if received_date_from is not None:
        params['received_date_from'] = received_date_from
    if received_date_to is not None:
        params['received_date_to'] = received_date_to
    if sent_date_from is not None:
        params['sent_date_from'] = sent_date_from
    if sent_date_to is not None:
        params['sent_date_to'] = sent_date_to
    if is_read is not None:
        params['is_read'] = is_read
    if is_draft is not None:
        params['is_draft'] = is_draft
    if has_attachments is not None:
        params['has_attachments'] = has_attachments
    if importance is not None:
        params['importance'] = importance
    if sensitivity is not None:
        params['sensitivity'] = sensitivity
    if inference_classification is not None:
        params['inference_classification'] = inference_classification
    if subject is not None:
        params['subject'] = subject
    if body_content is not None:
        params['body_content'] = body_content
    if body_preview is not None:
        params['body_preview'] = body_preview
    if subject_operator is not None:
        params['subject_operator'] = subject_operator
    if body_operator is not None:
        params['body_operator'] = body_operator
    if id is not None:
        params['id'] = id
    if conversation_id is not None:
        params['conversation_id'] = conversation_id
    if parent_folder_id is not None:
        params['parent_folder_id'] = parent_folder_id
    if categories is not None:
        params['categories'] = categories
    if flag_status is not None:
        params['flag_status'] = flag_status

    return params


def create_exclude_params(
    # 발신자 제외
    exclude_from_address: Optional[str] = None,
    exclude_sender_address: Optional[str] = None,
    # 키워드 제외
    exclude_subject_keywords: Optional[List[str]] = None,
    exclude_body_keywords: Optional[List[str]] = None,
    exclude_preview_keywords: Optional[List[str]] = None,
    # 속성 제외
    exclude_importance: Optional[Literal["low", "normal", "high"]] = None,
    exclude_sensitivity: Optional[Literal["normal", "personal", "private", "confidential"]] = None,
    exclude_classification: Optional[Literal["focused", "other"]] = None,
    # 상태 제외
    exclude_read_status: Optional[bool] = None,
    exclude_draft_status: Optional[bool] = None,
    exclude_attachment_status: Optional[bool] = None,
    # 플래그/카테고리 제외
    exclude_flag_status: Optional[Literal["notFlagged", "complete", "flagged"]] = None,
    exclude_categories: Optional[List[str]] = None,
    # ID 제외
    exclude_id: Optional[str] = None,
    exclude_conversation_id: Optional[str] = None,
    exclude_parent_folder_id: Optional[str] = None
) -> ExcludeParams:
    """ExcludeParams 객체를 생성하는 헬퍼 함수"""
    params: ExcludeParams = {}

    # 값이 None이 아닌 것만 추가
    if exclude_from_address is not None:
        params['exclude_from_address'] = exclude_from_address
    if exclude_sender_address is not None:
        params['exclude_sender_address'] = exclude_sender_address
    if exclude_subject_keywords is not None:
        params['exclude_subject_keywords'] = exclude_subject_keywords
    if exclude_body_keywords is not None:
        params['exclude_body_keywords'] = exclude_body_keywords
    if exclude_preview_keywords is not None:
        params['exclude_preview_keywords'] = exclude_preview_keywords
    if exclude_importance is not None:
        params['exclude_importance'] = exclude_importance
    if exclude_sensitivity is not None:
        params['exclude_sensitivity'] = exclude_sensitivity
    if exclude_classification is not None:
        params['exclude_classification'] = exclude_classification
    if exclude_read_status is not None:
        params['exclude_read_status'] = exclude_read_status
    if exclude_draft_status is not None:
        params['exclude_draft_status'] = exclude_draft_status
    if exclude_attachment_status is not None:
        params['exclude_attachment_status'] = exclude_attachment_status
    if exclude_flag_status is not None:
        params['exclude_flag_status'] = exclude_flag_status
    if exclude_categories is not None:
        params['exclude_categories'] = exclude_categories
    if exclude_id is not None:
        params['exclude_id'] = exclude_id
    if exclude_conversation_id is not None:
        params['exclude_conversation_id'] = exclude_conversation_id
    if exclude_parent_folder_id is not None:
        params['exclude_parent_folder_id'] = exclude_parent_folder_id

    return params


def create_select_params(
    fields: Optional[List[str]] = None
) -> SelectParams:
    """SelectParams 객체를 생성하는 헬퍼 함수"""
    params: SelectParams = {}
    if fields is not None:
        params['fields'] = fields
    return params


# 헬퍼 함수들 - 쿼리 빌드
def build_filter_query(params: FilterParams) -> str:
    """FilterParams를 Graph API $filter 쿼리 문자열로 변환"""
    filters = []

    # 발신자
    if params.get('from_address'):
        from_addr = params['from_address']
        if isinstance(from_addr, list):
            # 리스트인 경우 OR 조건으로 연결
            from_filters = [f"from/emailAddress/address eq '{addr}'" for addr in from_addr]
            if from_filters:
                filters.append(f"({' or '.join(from_filters)})")
        else:
            # 단일 문자열
            filters.append(f"from/emailAddress/address eq '{from_addr}'")

    if params.get('sender_address'):
        sender_addr = params['sender_address']
        if isinstance(sender_addr, list):
            # 리스트인 경우 OR 조건으로 연결
            sender_filters = [f"sender/emailAddress/address eq '{addr}'" for addr in sender_addr]
            if sender_filters:
                filters.append(f"({' or '.join(sender_filters)})")
        else:
            # 단일 문자열
            filters.append(f"sender/emailAddress/address eq '{sender_addr}'")

    # 날짜/시간 - 단일 날짜 필터 (ge 연산자만 사용 - 이후 날짜)
    if params.get('received_date_time'):
        filters.append(f"receivedDateTime ge {params['received_date_time']}")
    if params.get('sent_date_time'):
        filters.append(f"sentDateTime ge {params['sent_date_time']}")
    if params.get('created_date_time'):
        filters.append(f"createdDateTime ge {params['created_date_time']}")
    if params.get('last_modified_date_time'):
        filters.append(f"lastModifiedDateTime ge {params['last_modified_date_time']}")

    # 날짜 범위 필터 (from/to로 정확한 기간 지정)
    # received_date_time의 확장 버전 - 더 정밀한 날짜 범위 제어
    if params.get('received_date_from'):
        filters.append(f"receivedDateTime ge {params['received_date_from']}")
    if params.get('received_date_to'):
        filters.append(f"receivedDateTime le {params['received_date_to']}")
    if params.get('sent_date_from'):
        filters.append(f"sentDateTime ge {params['sent_date_from']}")
    if params.get('sent_date_to'):
        filters.append(f"sentDateTime le {params['sent_date_to']}")

    # 상태
    if params.get('is_read') is not None:
        filters.append(f"isRead eq {str(params['is_read']).lower()}")
    if params.get('is_draft') is not None:
        filters.append(f"isDraft eq {str(params['is_draft']).lower()}")
    if params.get('has_attachments') is not None:
        filters.append(f"hasAttachments eq {str(params['has_attachments']).lower()}")

    # 속성
    if params.get('importance'):
        filters.append(f"importance eq '{params['importance']}'")
    if params.get('sensitivity'):
        filters.append(f"sensitivity eq '{params['sensitivity']}'")
    if params.get('inference_classification'):
        filters.append(f"inferenceClassification eq '{params['inference_classification']}'")

    # 키워드 검색
    if params.get('subject'):
        subject = params['subject']
        if isinstance(subject, list):
            # 리스트인 경우 OR 또는 AND로 연결
            operator = params.get('subject_operator', 'or')  # 기본값 'or'
            subject_filters = [f"contains(subject, '{kw}')" for kw in subject]
            if subject_filters:
                if operator == 'and':
                    filters.extend(subject_filters)  # AND는 각각 추가
                else:  # or
                    filters.append(f"({' or '.join(subject_filters)})")
        else:
            # 단일 문자열
            filters.append(f"contains(subject, '{subject}')")

    if params.get('body_content'):
        body_content = params['body_content']
        if isinstance(body_content, list):
            # 리스트인 경우 OR 또는 AND로 연결
            operator = params.get('body_operator', 'or')  # 기본값 'or'
            body_filters = [f"contains(body/content, '{kw}')" for kw in body_content]
            if body_filters:
                if operator == 'and':
                    filters.extend(body_filters)  # AND는 각각 추가
                else:  # or
                    filters.append(f"({' or '.join(body_filters)})")
        else:
            # 단일 문자열
            filters.append(f"contains(body/content, '{body_content}')")

    if params.get('body_preview'):
        body_preview = params['body_preview']
        if isinstance(body_preview, list):
            # 리스트인 경우 OR로 연결 (preview는 보통 OR만 사용)
            preview_filters = [f"contains(bodyPreview, '{kw}')" for kw in body_preview]
            if preview_filters:
                filters.append(f"({' or '.join(preview_filters)})")
        else:
            # 단일 문자열
            filters.append(f"contains(bodyPreview, '{body_preview}')")

    # ID
    if params.get('id'):
        filters.append(f"id eq '{params['id']}'")
    if params.get('conversation_id'):
        filters.append(f"conversationId eq '{params['conversation_id']}'")
    if params.get('parent_folder_id'):
        filters.append(f"parentFolderId eq '{params['parent_folder_id']}'")

    # 카테고리
    if params.get('categories'):
        for category in params['categories']:
            filters.append(f"categories/any(c:c eq '{category}')")

    # 플래그
    if params.get('flag_status'):
        filters.append(f"flag/flagStatus eq '{params['flag_status']}'")

    return " and ".join(filters)


def build_exclude_query(params: ExcludeParams) -> str:
    """ExcludeParams를 Graph API 제외 쿼리 문자열로 변환"""
    excludes = []

    # 발신자 제외
    if params.get('exclude_from_address'):
        exclude_from = params['exclude_from_address']
        if isinstance(exclude_from, list):
            # 리스트인 경우 각각 ne 조건으로 추가
            for addr in exclude_from:
                excludes.append(f"from/emailAddress/address ne '{addr}'")
        else:
            # 단일 문자열
            excludes.append(f"from/emailAddress/address ne '{exclude_from}'")

    if params.get('exclude_sender_address'):
        exclude_sender = params['exclude_sender_address']
        if isinstance(exclude_sender, list):
            # 리스트인 경우 각각 ne 조건으로 추가
            for addr in exclude_sender:
                excludes.append(f"sender/emailAddress/address ne '{addr}'")
        else:
            # 단일 문자열
            excludes.append(f"sender/emailAddress/address ne '{exclude_sender}'")

    # 키워드 제외
    if params.get('exclude_subject_keywords'):
        for keyword in params['exclude_subject_keywords']:
            excludes.append(f"not contains(subject, '{keyword}')")
    if params.get('exclude_body_keywords'):
        for keyword in params['exclude_body_keywords']:
            excludes.append(f"not contains(body/content, '{keyword}')")
    if params.get('exclude_preview_keywords'):
        for keyword in params['exclude_preview_keywords']:
            excludes.append(f"not contains(bodyPreview, '{keyword}')")

    # 속성 제외
    if params.get('exclude_importance'):
        excludes.append(f"importance ne '{params['exclude_importance']}'")
    if params.get('exclude_sensitivity'):
        excludes.append(f"sensitivity ne '{params['exclude_sensitivity']}'")
    if params.get('exclude_classification'):
        excludes.append(f"inferenceClassification ne '{params['exclude_classification']}'")

    # 상태 제외
    if params.get('exclude_read_status') is not None:
        excludes.append(f"isRead ne {str(params['exclude_read_status']).lower()}")
    if params.get('exclude_draft_status') is not None:
        excludes.append(f"isDraft ne {str(params['exclude_draft_status']).lower()}")
    if params.get('exclude_attachment_status') is not None:
        excludes.append(f"hasAttachments ne {str(params['exclude_attachment_status']).lower()}")

    # 플래그 제외
    if params.get('exclude_flag_status'):
        excludes.append(f"flag/flagStatus ne '{params['exclude_flag_status']}'")

    # 카테고리 제외
    if params.get('exclude_categories'):
        for category in params['exclude_categories']:
            excludes.append(f"not categories/any(c:c eq '{category}')")

    # ID 제외
    if params.get('exclude_id'):
        excludes.append(f"id ne '{params['exclude_id']}'")
    if params.get('exclude_conversation_id'):
        excludes.append(f"conversationId ne '{params['exclude_conversation_id']}'")
    if params.get('exclude_parent_folder_id'):
        excludes.append(f"parentFolderId ne '{params['exclude_parent_folder_id']}'")

    return " and ".join(excludes)


def build_select_query(params: SelectParams) -> str:
    """SelectParams를 Graph API $select 쿼리 문자열로 변환"""
    if params.get('fields'):
        return ",".join(params['fields'])
    return ""


def build_complete_query(query_params: MailQueryParams) -> str:
    """전체 쿼리 파라미터를 URL 쿼리 문자열로 변환"""
    query_parts = []

    # 필터 조합
    filter_parts = []
    if query_params.get('filter'):
        filter_query = build_filter_query(query_params['filter'])
        if filter_query:
            filter_parts.append(filter_query)

    if query_params.get('exclude'):
        exclude_query = build_exclude_query(query_params['exclude'])
        if exclude_query:
            filter_parts.append(exclude_query)

    if filter_parts:
        query_parts.append(f"$filter={' and '.join(filter_parts)}")

    # Select
    if query_params.get('select'):
        select_query = build_select_query(query_params['select'])
        if select_query:
            query_parts.append(f"$select={select_query}")

    # 기타 옵션
    if query_params.get('top'):
        query_parts.append(f"$top={query_params['top']}")
    if query_params.get('skip'):
        query_parts.append(f"$skip={query_params['skip']}")
    if query_params.get('orderby'):
        query_parts.append(f"$orderby={query_params['orderby']}")
    if query_params.get('search'):
        query_parts.append(f"$search=\"{query_params['search']}\"")
    if query_params.get('count'):
        query_parts.append("$count=true")

    return "&".join(query_parts)


# 사용 예시
if __name__ == "__main__":
    # 예시 1: 기본 필터 파라미터
    filter_params: FilterParams = {
        "is_read": False,
        "has_attachments": True,
        "importance": "high",
        "subject": "회의"
    }

    # 예시 2: 날짜 범위 필터 사용 (2024년 10월 1일 ~ 10월 7일)
    date_range_params: FilterParams = {
        "received_date_from": "2024-10-01T00:00:00Z",  # 시작일 (포함)
        "received_date_to": "2024-10-07T23:59:59Z",    # 종료일 (포함)
        "is_read": False
    }

    # 예시 3: 단일 날짜 필터 vs 날짜 범위 필터
    # 단일 날짜 (특정 시점 이후 모든 메일)
    single_date_params: FilterParams = {
        "received_date_time": "2024-12-01T00:00:00Z"  # 12월 1일 이후 모든 메일
    }

    # 날짜 범위 (정확한 기간 지정)
    range_params: FilterParams = {
        "received_date_from": "2024-12-01T00:00:00Z",  # 12월 1일부터
        "received_date_to": "2024-12-07T23:59:59Z"     # 12월 7일까지
    }

    # 예시 4: 여러 발신자 조회 (리스트 사용)
    multiple_senders_params: FilterParams = {
        "from_address": ["boss@company.com", "manager@company.com", "ceo@company.com"],
        "received_date_from": "2024-12-01T00:00:00Z",
        "is_read": False
    }

    # 예시 5: 단일 발신자 vs 여러 발신자
    # 단일 발신자
    single_sender: FilterParams = {
        "from_address": "newsletter@company.com"
    }

    # 여러 발신자 (OR 조건으로 연결)
    multiple_senders: FilterParams = {
        "from_address": ["team1@company.com", "team2@company.com", "team3@company.com"]
    }

    # 예시 6: 키워드 검색 - 단일 vs 리스트
    # 단일 키워드
    single_keyword: FilterParams = {
        "subject": "프로젝트"
    }

    # 여러 키워드 (OR) - 제목에 '프로젝트' 또는 '회의' 포함
    keywords_or: FilterParams = {
        "subject": ["프로젝트", "회의", "미팅"],
        "subject_operator": "or"  # 기본값이므로 생략 가능
    }

    # 여러 키워드 (AND) - 제목에 '프로젝트'와 '승인' 모두 포함
    keywords_and: FilterParams = {
        "subject": ["프로젝트", "승인"],
        "subject_operator": "and"
    }

    # 예시 7: 복합 키워드 검색
    complex_keywords: FilterParams = {
        "subject": ["긴급", "중요"],  # 제목에 '긴급' 또는 '중요'
        "subject_operator": "or",
        "body_content": ["승인", "결재"],  # 본문에 '승인'과 '결재' 모두
        "body_operator": "and",
        "received_date_from": "2024-12-01T00:00:00Z"
    }

    # 제외 파라미터 설정 - 여러 발신자 제외
    exclude_params: ExcludeParams = {
        "exclude_from_address": ["noreply@github.com", "notification@slack.com", "no-reply@amazon.com"],
        "exclude_subject_keywords": ["newsletter", "광고", "홍보"]
    }

    # 선택 필드 설정
    select_params: SelectParams = {
        "fields": ["id", "subject", "from", "receivedDateTime", "hasAttachments"]
    }

    # 전체 쿼리 파라미터
    query: MailQueryParams = {
        "filter": filter_params,
        "exclude": exclude_params,
        "select": select_params,
        "top": 50,
        "orderby": "receivedDateTime desc"
    }

    # 쿼리 문자열 생성
    query_string = build_complete_query(query)
    print(f"Generated query: {query_string}")

    # 날짜 범위 필터 쿼리 생성
    date_range_query = build_filter_query(date_range_params)
    print(f"\n날짜 범위 필터: {date_range_query}")
    # 출력: receivedDateTime ge 2024-10-01T00:00:00Z and receivedDateTime le 2024-10-07T23:59:59Z and isRead eq false

    # 단일 날짜 vs 날짜 범위 비교
    single_query = build_filter_query(single_date_params)
    range_query = build_filter_query(range_params)
    print(f"\n단일 날짜 필터 (이후 모든 메일): {single_query}")
    print(f"날짜 범위 필터 (특정 기간): {range_query}")

    # 여러 발신자 필터 쿼리 생성
    multiple_senders_query = build_filter_query(multiple_senders_params)
    print(f"\n여러 발신자 필터: {multiple_senders_query}")
    # 출력: (from/emailAddress/address eq 'boss@company.com' or from/emailAddress/address eq 'manager@company.com' or from/emailAddress/address eq 'ceo@company.com') and receivedDateTime ge 2024-12-01T00:00:00Z and isRead eq false

    # 제외 쿼리 생성
    exclude_query = build_exclude_query(exclude_params)
    print(f"\n제외 필터: {exclude_query}")
    # 출력: from/emailAddress/address ne 'noreply@github.com' and from/emailAddress/address ne 'notification@slack.com' and from/emailAddress/address ne 'no-reply@amazon.com' and not contains(subject, 'newsletter') and not contains(subject, '광고') and not contains(subject, '홍보')

    # 키워드 필터 예시
    keywords_or_query = build_filter_query(keywords_or)
    keywords_and_query = build_filter_query(keywords_and)
    complex_query = build_filter_query(complex_keywords)

    print(f"\n키워드 OR 필터: {keywords_or_query}")
    # 출력: (contains(subject, '프로젝트') or contains(subject, '회의') or contains(subject, '미팅'))

    print(f"\n키워드 AND 필터: {keywords_and_query}")
    # 출력: contains(subject, '프로젝트') and contains(subject, '승인')

    print(f"\n복합 키워드 필터: {complex_query}")
    # 출력: (contains(subject, '긴급') or contains(subject, '중요')) and contains(body/content, '승인') and contains(body/content, '결재') and receivedDateTime ge 2024-12-01T00:00:00Z

    # 최종 URL 예시
    base_url = "https://graph.microsoft.com/v1.0/me/messages"
    full_url = f"{base_url}?{query_string}"
    print(f"\nFull URL: {full_url}")
    print(f"URL Length: {len(full_url)} characters")