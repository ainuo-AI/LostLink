"""测试数据工厂。

固定结构、相对当前时间的演示数据让筛选测试稳定，同时不包含真实个人信息。
"""

from datetime import UTC, datetime, timedelta

from app.schemas.item import Campus, CampusArea, ItemRead, ItemStatus, RecordType


def build_demo_items(now: datetime | None = None) -> list[ItemRead]:
    """构造六条进行中记录和一条关闭记录。"""

    current_time = now or datetime.now(UTC)
    return [
        ItemRead(
            id=1,
            type=RecordType.LOST,
            category="箱包",
            title="黑色双肩包",
            description="包上有一枚白色小熊徽章，内有专业课本和钥匙。",
            location="图书馆二层",
            campus=Campus.DONGLI,
            area=CampusArea.NORTH,
            occurred_at=current_time - timedelta(hours=2),
            status=ItemStatus.ACTIVE,
            contact_hint="请提供包内课本名称进行核验。",
        ),
        ItemRead(
            id=2,
            type=RecordType.FOUND,
            category="卡证",
            title="蓝色校园卡套",
            description="透明卡套配蓝色挂绳，已送到教学楼值班室。",
            location="教学楼 A 座",
            campus=Campus.DONGLI,
            area=CampusArea.SOUTH,
            occurred_at=current_time - timedelta(days=1),
            status=ItemStatus.ACTIVE,
            contact_hint="请说明卡套内校园卡的姓名末字。",
        ),
        ItemRead(
            id=3,
            type=RecordType.FOUND,
            category="数码",
            title="白色无线耳机",
            description="白色充电仓，外壳有轻微划痕，耳机已妥善保管。",
            location="操场南门",
            campus=Campus.NINGHE,
            occurred_at=current_time - timedelta(days=4),
            status=ItemStatus.ACTIVE,
            contact_hint="请描述蓝牙名称或保护套特征。",
        ),
        ItemRead(
            id=4,
            type=RecordType.LOST,
            category="文具",
            title="银色金属钢笔",
            description="笔帽处刻有一行小字，可能遗落在自习室。",
            location="博学楼 302",
            campus=Campus.DONGLI,
            area=CampusArea.NORTH,
            occurred_at=current_time - timedelta(days=5),
            status=ItemStatus.ACTIVE,
            contact_hint="请联系发布者进一步核对。",
        ),
        ItemRead(
            id=5,
            type=RecordType.FOUND,
            category="服饰",
            title="浅灰色防晒外套",
            description="左侧口袋内有一包纸巾，现放在食堂服务台。",
            location="第二食堂",
            campus=Campus.NINGHE,
            occurred_at=current_time - timedelta(days=6),
            status=ItemStatus.ACTIVE,
            contact_hint="请说明外套尺码和品牌。",
        ),
        ItemRead(
            id=6,
            type=RecordType.LOST,
            category="书籍",
            title="《软件工程导论》",
            description="书中夹有黄色便签，扉页写有姓名和班级。",
            location="实验楼 4 楼",
            campus=Campus.DONGLI,
            area=CampusArea.SOUTH,
            occurred_at=current_time - timedelta(days=8),
            status=ItemStatus.ACTIVE,
            contact_hint="请联系发布者核对扉页信息。",
        ),
        ItemRead(
            id=7,
            type=RecordType.LOST,
            category="其他",
            title="已关闭的演示记录",
            description="用于验证默认列表不会展示已关闭信息。",
            location="测试地点",
            campus=Campus.NINGHE,
            occurred_at=current_time - timedelta(days=2),
            status=ItemStatus.CLOSED,
            contact_hint="此记录仅用于自动测试。",
        ),
    ]
