select s.is_active 
from cms_blogentry be, cms_standardpage p, cms_basepage bp, cms_standardsection s
where be.standardpage_ptr_id = p.basepage_ptr_id
and bp.id = p.basepage_ptr_id
and s.id = bp.section_id
