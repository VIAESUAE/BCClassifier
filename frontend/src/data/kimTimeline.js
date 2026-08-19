export const KIM_WEXLER_EMAIL = 'k.wexler@hhm-law.com'

export function isKimDemoCard(card) {
  return (card?.email || '').toLowerCase() === KIM_WEXLER_EMAIL
}

export const KIM_CONTACT = {
  fullName: 'Kim Wexler',
  title: '合伙人 · 商事与合规',
  firm: 'Hamlin, Hamlin & McGill',
  email: KIM_WEXLER_EMAIL,
  locale: 'Albuquerque · CN Desk',
}

export const KIM_NOW = '2026-08-11'

export const KIM_MAILS = [
  {
    id: 'm0',
    side: 'them',
    sent: '2026-05-12',
    ddl: '2026-08-28',
    subject: 'Mesa Verde 案件进展说明',
    summary:
      'Kim 通报 Mesa Verde 案件当前进展，并列出下一阶段需双方对齐的材料与节点。请于截止日期前完成相关回复。',
    ddlNote: '2026年8月28日前完成案件相关材料确认与书面回复。',
  },
  {
    id: 'm1',
    side: 'us',
    sent: '2026-06-12',
    ddl: '2026-06-20',
    subject: '初步合作意向与保密框架',
    summary:
      '向贵所发出合作意向说明，并附保密框架草案。请在确认可受理本事项后，于截止日期前书面回复是否进入正式磋商。',
    ddlNote: '2026年6月20日前确认是否接受 nondisclosure 框架并进入磋商。',
  },
  {
    id: 'm2',
    side: 'them',
    sent: '2026-06-18',
    ddl: null,
    subject: '关于保密条款的原则性同意',
    summary:
      'Kim 原则同意保密框架方向，并就管辖与例外披露条款提出两处措辞调整建议，征求我方意见。本件无硬性截止日期。',
    ddlNote: null,
  },
  {
    id: 'm3',
    side: 'us',
    sent: '2026-07-02',
    ddl: '2026-07-15',
    subject: '尽职调查材料清单',
    summary:
      '正式启动尽调程序。请贵所协调客户于截止日期前提供近三年工商档案、重大诉讼与仲裁清单，以及关联方资金往来说明。',
    ddlNote: '2026年7月15日前提交完整尽调材料包。',
  },
  {
    id: 'm4',
    side: 'them',
    sent: '2026-07-10',
    ddl: '2026-07-14',
    subject: '核心材料递交时间说明',
    summary:
      '确认诉讼清单与工商档案已齐备；关联方说明尚在整理。Kim 承诺核心材料将于截止日期前送达，其余附件可于其后两个工作日补齐。',
    ddlNote: '2026年7月14日前送达核心尽调材料。',
  },
  {
    id: 'm4b',
    side: 'us',
    sent: '2026-07-15',
    ddl: '2026-08-05',
    subject: '中期法律意见书提交安排',
    summary:
      '基于已收到的核心尽调材料，我方启动中期法律意见书起草。请双方于截止日期前完成事实核对与意见书定稿，作为框架协议谈判的前置输入。',
    ddlNote: '2026年8月5日前完成中期法律意见书定稿并双向确认。',
  },
  {
    id: 'm5',
    side: 'us',
    sent: '2026-07-28',
    ddl: '2026-08-20',
    subject: '合作关系确认与框架协议回签',
    summary:
      '尽调初步结论可支持推进。请双方于截止日期前确认合作关系，并完成框架协议回签；逾期将重新评估排期与费率安排。',
    ddlNote: '2026年8月20日前确认合作关系并回签框架协议。',
  },
  {
    id: 'm6',
    side: 'them',
    sent: '2026-08-05',
    ddl: null,
    subject: '框架协议第4条意见征询',
    summary:
      'Kim 就赔偿上限与提前终止通知期征求我方书面意见，便于其内部合伙人会议讨论。本件为意见征询，未设定正式 DDL。',
    ddlNote: null,
  },
]
