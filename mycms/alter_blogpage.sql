alter table cms_blogpage add column user_id integer;

alter table cms_blogpage add CONSTRAINT cms_blog_user_id_fkey FOREIGN KEY (user_id)
      REFERENCES auth_user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

alter table cms_blogpage add CONSTRAINT cms_blogpage_user_id_key UNIQUE (user_id);

--alter table cms_blogpage drop constraint cms_blog_user_id_fkey;

alter table cms_userprofile add column nickname character varying(30);

alter table cms_userprofile add CONSTRAINT cms_userprofile_nickname_key UNIQUE (nickname);

