#!/usr/bin/env python

import logging
from flask import jsonify
import datetime

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement


class SPSDBManager:
    def __init__(self,sps_keyspacename,sps_tablename):
        self.sps_keyspacename = sps_keyspacename;
        self.sps_tablename = sps_tablename;

    def initializeDB(self):
        cluster = Cluster(['127.0.0.1'])
        self.session = cluster.connect()

    def createKeySpace(self):
        log.info("creating keyspace...")
        self.session.execute("""
            CREATE KEYSPACE %s
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """ % self.sps_keyspacename)

        log.info("setting keyspace...")
        #session.set_keyspace(SPS_keyspaceName)

    def createTable(self):
        log.info("creating table...")
        self.session.execute("""
            CREATE TABLE %s.%s (
                job_id int,
                start_time timestamp,
                end_time timestamp,
                roll_count int,
                ip text,
                state text,
                analysis text,
                PRIMARY KEY (job_id, ip)
            )
            """ % (self.sps_keyspacename, self.sps_tablename))
        log.info("table created");

    def dropKeyspace(self):
        self.session.execute("DROP KEYSPACE " + self.sps_keyspacename)    

    def SetUpDB(self):
        self.initializeDB();
        if self.session is None :
            log.info("seesion not retuned")
            return;

        self.dropKeyspace();
        self.createKeySpace();
        self.createTable();
        log.info("table created");

        jobObj = {
        'job_id': 1,
        'start_time': datetime.datetime(2016,9,23), #"23 Nov 2016",
        'end_time': datetime.datetime(2016,9,23),
        'roll_count':101,
        'ip':"127.0.0.1",
        'state':"pending",
        'analysis':"unknown"
        };
        self.addNewJob(jobObj);

    def addNewJob(self, jobObject):
        stmt = self.session.prepare("""
        INSERT INTO %s.%s (job_id, start_time, end_time,roll_count,ip,state,analysis)
        VALUES (?,?,?,?,?,?,?) 
        IF NOT EXISTS
        """ %(self.sps_keyspacename, self.sps_tablename))
        
        self.session.execute(stmt,[jobObject['job_id'],jobObject['start_time'],jobObject['end_time'],jobObject['roll_count'],jobObject['ip'],jobObject['state'],jobObject['analysis']])


    def selectAllJobs(self):
        future = self.session.execute_async("""SELECT * FROM %s.%s""" %(self.sps_keyspacename, self.sps_tablename))
        try:
            rows = future.result()
        except Exception:
            log.exeception()

        for row in rows:
            log.info('\t'.join(row))

    def emptyFunc():
        log.info("empty")


if __name__ == "__main__":
    dbmgr = SPSDBManager(sps_keyspacename='SPS_KEYSPACE', sps_tablename='SPS_TABLE')
    dbmgr.SetUpDB()
