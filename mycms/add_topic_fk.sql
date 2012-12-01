alter table cms_blogentry
add column topic_id integer;

ALTER TABLE cms_blogentry ADD FOREIGN KEY (topic_id) REFERENCES cms_blogentrytopic(id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;
