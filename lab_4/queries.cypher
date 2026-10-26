CREATE (s:Student {
    name:"Nikhil",
    rollNo: 66,
    course:"Computer Engieering"
})

MATCH (s:Student)
where s.name = null
DELETE s

MATCH (s:Student) 
WHERE s.name = "null" 
DELETE s

create (t:Todo { title:"Learn Cypher",completed:FALSE
  }),(t2:Todo{
    title:"Learn Neo4j"
    completed:FALSE
  }),(t3:Todo{
    title:"Learn Graph Databases"
    completed:FALSE
  })

create (cat:Category {title:"Work"})

match (
  t:Todo {title:"Learn Cypher"},
  cat:Category { title:"Work" }
)
CREATE (t)-[:TYPE_OF]->(cat)

match (
  t:Todo {title:"Learn Graph Databases"},
  cat:Category { title:"Work" }
)
CREATE (t)-[:TYPE_OF]->(cat)

match (
  t:Todo {title:"Learn Neo4j"},
  cat:Category { title:"Work" }
)
CREATE (t)-[:TYPE_OF]->(cat)

match [n]->[r]->[m]
return n,r,m

create ( u:User { name:"Nikhil" })

CREATE
(u1:User {
    name: "Nikhil",
    email:"nikhil@gmail.com"
}),
(u2:User {
    name: "Amit",
    rollNo: 67,
    course: "Computer Engineering"
    email:"amit@gmail.com"
});
