CREATE TABLE cms_blogentry_sav
(
  standardpage_ptr_id integer NOT NULL,
  blog_id integer,
  comment_allowed character varying(1) NOT NULL,
  topic_id integer
);

insert into cms_blogentry_sav(standardpage_ptr_id, blog_id, comment_allowed, topic_id)
select standardpage_ptr_id, blog_id, comment_allowed, topic_id from cms_blogentry;

commit;

insert into cms_blogentry(standardpage_ptr_id, blog_id, comment_allowed)
select standardpage_ptr_id, blog_id, comment_allowed from cms_blogentry_sav;




rollback;
