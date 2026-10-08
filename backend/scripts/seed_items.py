"""向空数据库写入不含个人信息的演示记录。

脚本只在 items 表为空时写入，避免重复执行产生重复演示数据。
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.item import Item


def seed_items(session: Session) -> bool:
    """为空表写入演示记录；写入时返回 True，已有数据时返回 False。"""

    if session.scalar(select(func.count()).select_from(Item)):
        return False

    # MySQL DATETIME 按项目约定保存无时区的 UTC 值。
    now = datetime.now(UTC).replace(tzinfo=None)
    session.add_all(
        [
            Item(
                type="lost",
                category="箱包",
                title="黑色双肩包",
                description="包上有一枚白色小熊徽章，内有专业课本和钥匙。",
                location="图书馆",
                campus="东丽校区",
                area="北区",
                occurred_at=now - timedelta(hours=2),
                status="active",
                contact_hint="请提供包内课本名称进行核验。",
            ),
            Item(
                type="found",
                category="卡证",
                title="蓝色校园卡套",
                description="透明卡套配蓝色挂绳，已送到教学楼值班室。",
                location="教学楼 A 座",
                campus="东丽校区",
                area="南区",
                occurred_at=now - timedelta(days=1),
                status="active",
                contact_hint="请说明卡套内校园卡的姓名末字。",
            ),
            Item(
                type="found",
                category="数码",
                title="白色无线耳机",
                description="白色充电仓，外壳有轻微划痕，耳机已妥善保管。",
                location="操场南门",
                campus="宁河校区",
                area=None,
                occurred_at=now - timedelta(days=4),
                status="active",
                contact_hint="请描述蓝牙名称或保护套特征。",
            ),
            Item(
                type="lost",
                category="文具",
                title="银色金属钢笔",
                description="笔帽处刻有一行小字，可能遗落在自习室。",
                location="博学楼",
                campus="东丽校区",
                area="北区",
                occurred_at=now - timedelta(days=5),
                status="active",
                contact_hint="请联系发布者进一步核对。",
            ),
            Item(
                type="found",
                category="服饰",
                title="浅灰色防晒外套",
                description="左侧口袋内有一包纸巾，现放在食堂服务台。",
                location="第二食堂",
                campus="宁河校区",
                area=None,
                occurred_at=now - timedelta(days=6),
                status="active",
                contact_hint="请说明外套尺码和品牌。",
            ),
            Item(
                type="lost",
                category="书籍",
                title="《软件工程导论》",
                description="书中夹有黄色便签，扉页写有姓名和班级。",
                location="实验楼",
                campus="东丽校区",
                area="南区",
                occurred_at=now - timedelta(days=8),
                status="active",
                contact_hint="请联系发布者核对扉页信息。",
            ),
            Item(
                type="lost",
                category="其他",
                title="已关闭的演示记录",
                description="用于验证默认列表不会展示已关闭信息。",
                location="宁河校区南门",
                campus="宁河校区",
                area=None,
                occurred_at=now - timedelta(days=2),
                status="closed",
                contact_hint="此记录仅用于自动测试。",
            ),
        ]
    )
    session.commit()
    return True


def main() -> None:
    """创建会话、执行幂等写入并输出简短结果。"""

    with SessionLocal() as session:
        inserted = seed_items(session)
    print("演示数据写入完成。" if inserted else "items 表已有数据，未重复写入。")


if __name__ == "__main__":
    main()
