Templates for `brainrc new skill|agent|rule|command` (brainrc/newitem.py): the body of each item,
under the frontmatter brainrc.scaffold writes. `{{key}}` is replaced by the item's value (name,
title, description, files). Keep them short: a rule's template loads in every session, and every
body is what a pack author starts from.
